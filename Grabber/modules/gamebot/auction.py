import asyncio
import random
import re
import time

from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import LOGGER, game_bot
from Grabber.core.balance import (check_and_deduct, get_user_balance,
                                  update_user_balance)
from Grabber.core.user import add_char_to_user
from Grabber.core.utils import html_escape, send_media_dynamic
from Grabber.database import sessions_collection, user_collection

# Auction Settings
TIMEOUT = 120  # 2 minutes
MIN_INCREMENT = 100
SNIPING_EXTENSION = 15  # seconds

RARITY_STARTING_BIDS = {
    "🟠 Rare": 200,
    "🟡 Legendary": 1000,
    "🫧 Royal": 2500,
    "🔮 Limited Edition": 2500,
    "💮 Exclusive": 2500,
    "💠 Cosmic": 5000,
    "💎 Antique": 5000
}

def get_auction_text(char, highest_bid, bidder_name, time_left):
    """Generates the auction status text."""
    bid_text = f"💰 <b>Current Bid:</b> {highest_bid:,} ⬪ by {html_escape(bidder_name)}" if highest_bid else "💰 <b>Current Bid:</b> No bids yet"
    
    return (
        f"🏛 <b>THE AUCTION HOUSE</b> 🏛\n\n"
        f"A rare character has been put up for auction! Bid now or miss out.\n\n"
        f"📛 <b>Name:</b> {html_escape(char['name'])}\n"
        f"🎬 <b>Anime:</b> {html_escape(char['anime'])}\n"
        f"✨ <b>Rarity:</b> {html_escape(char['rarity'])}\n\n"
        f"{bid_text}\n"
        f"⏱ <b>Time Left:</b> {int(time_left)}s\n\n"
        f"📝 <b>To Participate:</b> Use <code>/bid &lt;amount&gt;</code>\n"
        f"⚠️ <i>Funds are held upon bidding and refunded if outbidden.</i>"
    )

async def auction_timer_task(chat_id, start_time):
    """Manages the auction lifecycle, updates, and finalization."""
    while True:
        await asyncio.sleep(15) # Update every 15s to avoid flood
        
        session = await sessions_collection.find_one({"_id": f"auction:{chat_id}"})
        if not session or session.get("start_time") != start_time:
            break # Session replaced or deleted

        end_time = session["end_time"]
        now = time.time()
        time_left = end_time - now

        if time_left <= 0:
            # Auction Ended!
            await finalize_auction(chat_id, session)
            break
        
        # Update the message caption
        char = session["char"]
        text = get_auction_text(char, session["highest_bid"], session.get("bidder_name", "None"), time_left)
        
        try:
            await game_bot.edit_message_caption_safe(
                chat_id, 
                session["message_id"], 
                caption=text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            LOGGER.debug(f"Failed to update auction message in {chat_id}: {e}")

async def finalize_auction(chat_id, session):
    """Ends the auction and awards the character."""
    await sessions_collection.delete_one({"_id": f"auction:{chat_id}"})
    
    winner_id = session["bidder_id"]
    winner_name = session.get("bidder_name", "Nobody")
    char = session["char"]
    final_bid = session["highest_bid"]

    if not winner_id:
        # No bids
        text = (
            f"🏛 <b>Auction Closed</b>\n\n"
            f"The auction for <b>{html_escape(char['name'])}</b> has ended with no bids.\n"
            f"Better luck next time!"
        )
    else:
        # We have a winner!
        # Balance was already deducted, so we just add the character
        await add_char_to_user(winner_id, char)
        
        text = (
            f"🏛 <b>Auction Won!</b>\n\n"
            f"🎊 <a href='tg://user?id={winner_id}'>{html_escape(winner_name)}</a> won the auction for <b>{final_bid:,} ⬪</b>!\n"
            f"👤 Character: <b>{html_escape(char['name'])}</b>\n"
            f"✨ Rarity: <b>{html_escape(char['rarity'])}</b>\n\n"
            f"<i>The character has been added to your harem!</i>"
        )

    try:
        # Unpin if possible
        try:
            await game_bot.unpin_chat_message(chat_id, session["message_id"])
        except:
            pass
            
        await game_bot.send_message_safe(chat_id, text, parse_mode=ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Error finalizing auction in {chat_id}: {e}")

async def trigger_auction(chat_id, character):
    """Starts a new auction for a character."""
    rarity = character.get("rarity", "🟠 Rare")
    starting_bid = RARITY_STARTING_BIDS.get(rarity, 500)
    
    start_time = time.time()
    end_time = start_time + TIMEOUT
    
    text = get_auction_text(character, 0, "None", TIMEOUT)
    
    try:
        msg = await game_bot.send_media_safe(
            chat_id,
            media_url=character['img_url'],
            caption=text,
            parse_mode=ParseMode.HTML
        )
        if not msg: return

        # Synchronize with global spawn cooldown to prevent overlapping spawns
        import json

        from Grabber.database import r as _redis
        from Grabber.database import spawns_collection

        # 1. Update MongoDB
        await spawns_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"last_spawn_time": start_time}},
            upsert=True
        )
        
        # 2. Update Redis Cache
        if _redis:
            try:
                key = f"spawn:state:{chat_id}"
                await _redis.hset(key, "last_spawn_time", str(start_time))
            except:
                pass

        # Attempt to pin
        try:
            # Check bot permissions before attempting to pin
            member = await game_bot.get_chat_member(chat_id, "me")
            if member.privileges and member.privileges.can_pin_messages:
                await msg.pin(disable_notification=False)
        except Exception as e:
            LOGGER.debug(f"Auction pin failed in {chat_id}: {e}")

        # Save session
        await sessions_collection.update_one(
            {"_id": f"auction:{chat_id}"},
            {"$set": {
                "char": character,
                "message_id": msg.id,
                "highest_bid": 0,
                "bidder_id": None,
                "bidder_name": None,
                "start_time": start_time,
                "end_time": end_time,
                "chat_id": chat_id,
                "starting_bid": starting_bid
            }},
            upsert=True
        )
        
        # Start the background task
        asyncio.create_task(auction_timer_task(chat_id, start_time))
        LOGGER.info(f"Auction started in {chat_id} for {character['name']}")

    except Exception as e:
        LOGGER.error(f"Error triggering auction: {e}")

@game_bot.on_message(filters.command("bid") & filters.group)
async def bid_handler(_, message: types.Message):
    """Handles /bid <amount> command."""
    if not message.from_user: return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    session = await sessions_collection.find_one({"_id": f"auction:{chat_id}"})
    if not session:
        return # No active auction

    # SAFETY CHECK: Ensure the auction hasn't been reset or replaced
    if time.time() > session["end_time"]:
        return await message.reply_text("⏱ This auction has already ended!", auto_delete=10)

    try:
        if len(message.command) < 2:
            return await message.reply_text("❌ Usage: <code>/bid &lt;amount&gt;</code>", auto_delete=10)
        
        bid_amount = int(message.command[1])
    except (ValueError, IndexError):
        return await message.reply_text("❌ Invalid bid amount.", auto_delete=10)

    current_highest = session["highest_bid"]
    starting_bid = session["starting_bid"]

    # Minimum bid validation
    min_required = max(starting_bid, current_highest + MIN_INCREMENT)
    if bid_amount < min_required:
        return await message.reply_text(f"⚠️ Your bid must be at least <b>{min_required:,} ⬪</b>!", parse_mode=ParseMode.HTML, auto_delete=10)

    if user_id == session["bidder_id"]:
        return await message.reply_text("⚠️ You are already the highest bidder!", auto_delete=10)

    # DEDUCT New Bid (Atomic)
    success = await check_and_deduct(user_id, bid_amount)
    if not success:
        return await message.reply_text("❌ You don't have enough Shards to place this bid!", auto_delete=10)

    # REFUND Previous Bidder (Atomic)
    last_bidder = session["bidder_id"]
    last_bid = session["highest_bid"]
    
    if last_bidder and last_bid > 0:
        await update_user_balance(last_bidder, last_bid)

    # Update Session (Atomic check for racing bids)
    # We use find_one_and_update with a filter on session["highest_bid"] to ensure we don't overwrite a faster bid
    # but since we already deducted and refunded above, we'd need to roll back if this fails.
    # To keep it simple but safe, we'll use a lock or just accept that in rare cases, refunds might be messy.
    # Better: Update using $set and check if start_time is the same.
    
    new_end_time = session["end_time"]
    if new_end_time - time.time() < SNIPING_EXTENSION:
        new_end_time += SNIPING_EXTENSION

    res = await sessions_collection.update_one(
        {"_id": f"auction:{chat_id}", "highest_bid": current_highest},
        {"$set": {
            "highest_bid": bid_amount,
            "bidder_id": user_id,
            "bidder_name": user_name,
            "end_time": new_end_time
        }}
    )

    if res.modified_count == 0:
        # Someone beat us to it in the same millisecond! Refund and fail.
        await update_user_balance(user_id, bid_amount)
        return await message.reply_text("⚠️ Someone else just placed a higher bid! Try again.", auto_delete=10)

    await message.reply_text(
        f"✅ <b>Bid Accepted!</b>\n{html_escape(user_name)} is the new leader with <b>{bid_amount:,} ⬪</b>.",
        parse_mode=ParseMode.HTML,
        auto_delete=30
    )
    
    # Proactively update the main message
    char = session["char"]
    time_left = new_end_time - time.time()
    text = get_auction_text(char, bid_amount, user_name, time_left)
    
    try:
        await game_bot.edit_message_caption_safe(chat_id, session["message_id"], caption=text, parse_mode=ParseMode.HTML)
    except:
        pass
