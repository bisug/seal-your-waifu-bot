import asyncio
import random
from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError
from pyrogram import enums, filters, types

from backend.client import app
from backend.core.balance import update_user_balance
from backend.core.rarities import CLAIM_RARITY_WEIGHTS, weighted_pick
from backend.core.user import add_char_to_user
from backend.core.utils import get_user_id_query, handle_errors, html_escape, reply_media_dynamic
from backend.core.waifu import sample_character_by_rarity
from backend.database import user_collection

start_messages = [
    "Finally the time has come",
    "The moment you've been waiting for",
    "The stars align for this proposal"
]
rejection_captions = [
    "She slapped you and ran away.",
    "She rejected you outright!",
    "You got a harsh 'NO!'"
]
acceptance_images = [
    "https://te.legra.ph/file/4fe133737bee4866a3549.png",
    "https://te.legra.ph/file/28d46e4656ee2c3e7dd8f.png",
    "https://te.legra.ph/file/d32c6328c6d271dd00816.png"
]
rejection_images = [
    "https://te.legra.ph/file/d6e784e5cda62ac27541f.png",
    "https://te.legra.ph/file/e4e1ba60b4e79359bf9e7.png",
    "https://te.legra.ph/file/81d011398da3a6f49fa7f.png"
]
async def get_random_waifu():
    rarity = weighted_pick(CLAIM_RARITY_WEIGHTS)
    if rarity is None:
        return None
    return await sample_character_by_rarity(rarity)
@app.on_message(filters.command("propose"))
@handle_errors
async def propose_command(_, message: types.Message):
    user_id = message.from_user.id
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Atomic once-per-day claim: the $ne guard folds the read-then-write into a
    # single conditional update, so concurrent /propose calls can't both grant.
    try:
        claim = await user_collection.update_one(
            {**get_user_id_query(user_id), "last_propose_date": {"$ne": now_date}},
            {"$set": {"last_propose_date": now_date}, "$setOnInsert": {"id": user_id}},
            upsert=True,
        )
    except DuplicateKeyError:
        # Concurrent propose won the race; the unique id index blocked the insert.
        return await message.reply_text("<b>You have already proposed today! Come back tomorrow.</b>", parse_mode=enums.ParseMode.HTML)
    if claim.modified_count == 0 and claim.upserted_id is None:
        return await message.reply_text("<b>You have already proposed today! Come back tomorrow.</b>", parse_mode=enums.ParseMode.HTML)
    start_msg = random.choice(start_messages)
    roll_text = random.choice(["Proposing her....", "Getting down on one knee....", "Popping the question...."])
    await message.reply_text(f"{start_msg}\n\n<b>{roll_text}</b>", parse_mode=enums.ParseMode.HTML)
    await asyncio.sleep(2)
    roll = random.uniform(0, 100)
    if roll < 3:
        char = await get_random_waifu()
        if char:
            await add_char_to_user(user_id, char)
            caption = (
                f"<b>Proposal Accepted!</b>\n\n"
                f"<b>{html_escape(char['name'])}</b> has accepted your proposal!\n"
                f"<b>Name:</b> {html_escape(char['name'])}\n"
                f"<b>Rarity:</b> {html_escape(char['rarity'])}\n"
                f"<b>Anime:</b> {html_escape(char['anime'])}"
            )
            img_url = char['img_url']
            await reply_media_dynamic(message, img_url, caption=caption, parse_mode=enums.ParseMode.HTML)
        else:
            await update_user_balance(user_id, 2000)
            await message.reply_text("<b>Proposal Accepted!</b>\nHowever, she was too shy to appear. You found <code>2,000</code> Shards instead!", parse_mode=enums.ParseMode.HTML)
    elif roll < 13:
        await update_user_balance(user_id, 2000)
        img = random.choice(acceptance_images)
        await reply_media_dynamic(message, img, caption="<b>Proposal Accepted!</b>\nShe was flattered but busy. She sent you <b>2,000 Shards</b> as a gift!", parse_mode=enums.ParseMode.HTML)
    elif roll < 43:
        await update_user_balance(user_id, 500)
        img = random.choice(acceptance_images)
        await reply_media_dynamic(message, img, caption="<b>Proposal Accepted!</b>\nShe smiled and gave you <b>500 Shards</b> for your effort!", parse_mode=enums.ParseMode.HTML)
    else:
        img = random.choice(rejection_images)
        caption = random.choice(rejection_captions)
        await reply_media_dynamic(message, img, caption=f"<b>Rejection!</b>\n{caption}", parse_mode=enums.ParseMode.HTML)
