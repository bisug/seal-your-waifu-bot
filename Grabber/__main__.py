#!/usr/bin/env python3
"""
🔥 Ultimate Waifu Grabber - Grabber Compatible 🔥
Uses YOUR existing Grabber imports + variables exactly as before.
Supports PTB application for your modules + optimized waifu game.
"""

import asyncio
import importlib
import logging
import random
import time
from html import escape
from typing import Dict, List

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import CommandHandler, MessageHandler, filters as ptb_filters

# === YOUR ORIGINAL IMPORTS (EXACTLY AS BEFORE) ===
from Grabber import (
    collection, 
    db, 
    user_collection, 
    message_counts_collection,
    application,  # Your PTB application
    LOGGER, 
    user_totals_collection, 
    Grabberu  # Your Pyrogram client
)
from Grabber.modules import ALL_MODULES

# Constants (same as your original)
SPECIAL_GROUP_ID = -1002528887253
ROYAL_NOTIFY_USER_ID = 7717913705

# === Globals (same structure) ===
locks: Dict[str, asyncio.Lock] = {}
message_counts: Dict[str, int] = {}
waifu_spawn_order: Dict[str, int] = {}
last_characters: Dict[int, Dict] = {}
first_correct_guesses: Dict[int, int | None] = {}
warned_users: Dict[tuple[int, int], float] = {}
rarity_char_cache: Dict[str, List[Dict]] = {}

rarity_spawn_order = ["⚪ Common", "🟢 Medium", "🟠 Rare", "🟡 Legendary"]
special_rarity_thresholds = {
    "💠 Cosmic": 300,
    "💮 Exclusive": 600,
    "🔮 Limited Edition": 900,
    "🫧 Royal": 1000,
}

# === Utils ===
def normalize_tokens(text: str) -> List[str]:
    return [t for t in text.lower().split() if t]

# === OPTIMIZED INITIALIZATION ===
async def preload_characters():
    global rarity_char_cache
    rarity_char_cache.clear()
    cursor = collection.find({})
    async for doc in cursor:
        rarity = doc.get("rarity")
        if rarity:
            rarity_char_cache.setdefault(rarity, []).append(doc)
    LOGGER.info(f"🚀 Cached: { {r: len(lst) for r, lst in rarity_char_cache.items()} }")

async def load_message_counts():
    global message_counts
    cursor = message_counts_collection.find({})
    async for doc in cursor:
        message_counts[str(doc["chat_id"])] = doc["count"]

async def save_message_counts():
    for chat_id, count in message_counts.items():
        await message_counts_collection.update_one(
            {"chat_id": chat_id}, {"$set": {"count": count}}, upsert=True
        )

# === PYROGRAM HANDLERS (Primary - Fast!) ===
@Grabberu.on_message(
    (filters.text | filters.photo | filters.video | filters.sticker)
    & ~filters.command(["seal", "messagecount"])
    & filters.group
)
async def pyro_message_counter(client, message: Message):
    chat_id_int = message.chat.id
    chat_id = str(chat_id_int)
    
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    async with locks[chat_id]:
        count = message_counts.get(chat_id)
        if count is None:
            data = await message_counts_collection.find_one({"chat_id": chat_id})
            count = data["count"] if data else 0
        count += 1
        message_counts[chat_id] = count

        chat_settings = await user_totals_collection.find_one({"chat_id": chat_id}) or {}
        message_frequency = chat_settings.get("message_frequency", 100)

        spawned = False
        for rarity, threshold in special_rarity_thresholds.items():
            if count % threshold == 0:
                if rarity == "🫧 Royal" and chat_id_int != SPECIAL_GROUP_ID:
                    continue
                await send_character(client, message, rarity)
                spawned = True
                break

        if not spawned and count % message_frequency == 0:
            idx = waifu_spawn_order.get(chat_id, 0)
            rarity = rarity_spawn_order[idx % len(rarity_spawn_order)]
            waifu_spawn_order[chat_id] = idx + 1
            await send_character(client, message, rarity)

        if count % 200 == 0:
            await save_message_counts()

async def send_character(client, message: Message, rarity: str):
    chat_id = message.chat.id
    
    candidates = rarity_char_cache.get(rarity)
    if not candidates:
        candidates = await collection.find({"rarity": rarity}).to_list(length=None)
        if not candidates:
            return

    grabber_id = first_correct_guesses.get(chat_id)
    if grabber_id is not None:
        last_grabber = await user_collection.find_one({"id": grabber_id})
        last_grabber_name = (last_grabber or {}).get("first_name", "Unknown User")
        await client.send_message(
            chat_id,
            f'⚠ Waifu grabbed by <a href="tg://user?id={grabber_id}">{escape(last_grabber_name)}</a>',
            parse_mode="HTML",
        )

    character = random.choice(candidates)
    last_characters[chat_id] = character
    first_correct_guesses[chat_id] = None

    caption = "🪽 New waifu!\n🦋 /seal name to claim!\n👑 Rarity on seal!"
    
    try:
        await client.send_photo(chat_id, photo=character["img_url"], caption=caption, parse_mode="HTML")
    except Exception as e:
        LOGGER.error(f"Photo failed: {e}")
        await client.send_message(chat_id, "⚠️ Image failed.")

    if rarity == "🫧 Royal":
        try:
            await client.send_message(
                ROYAL_NOTIFY_USER_ID,
                f"👑 ROYAL SPAWN!\nChat: {message.chat.title or chat_id}\nID: {character.get('id')}",
            )
        except Exception:
            pass

@Grabberu.on_message(filters.command("seal"))
async def pyro_seal(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user = message.from_user

    character = last_characters.get(chat_id)
    if not character:
        return

    grabber_id = first_correct_guesses.get(chat_id)
    if grabber_id is not None:
        last_grabber = await user_collection.find_one({"id": grabber_id})
        await message.reply(
            f'⚠ Already grabbed by <a href="tg://user?id={grabber_id}">{escape((last_grabber or {}).get("first_name", "Unknown"))}</a>',
            parse_mode="HTML",
        )
        return

    now = time.time()
    key = (chat_id, user_id)
    if warned_users.get(key, 0) > now - 1.0:
        return
    warned_users[key] = now

    guess_text = " ".join(message.command[1:])
    guess_tokens = normalize_tokens(guess_text)
    name_tokens = normalize_tokens(character["name"])

    if len(guess_tokens) == len(name_tokens) and sorted(guess_tokens) == sorted(name_tokens):
        first_correct_guesses[chat_id] = user_id
        await user_collection.update_one(
            {"id": user_id}, {"$push": {"characters": character}}, upsert=True
        )

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Harem", switch_inline_query_current_chat=f"collection.{user_id}")]])
        await message.reply(
            f"💫 <b>{escape(user.first_name)}</b> grabbed!\n"
            f"🎗 <b>{escape(character['name'])}</b>\n"
            f"🏵 <b>{escape(character['anime'])}</b>\n"
            f"🎮 <b>{escape(character['rarity'])}</b>",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await message.reply("❌ Wrong name!")

@Grabberu.on_message(filters.command("messagecount"))
async def pyro_msgcount(client, message: Message):
    chat_id = str(message.chat.id)
    count = message_counts.get(chat_id)
    if count is None:
        data = await message_counts_collection.find_one({"chat_id": chat_id})
        count = data["count"] if data else 0
    await message.reply(f"📨 Messages: <code>{count:,}</code>", parse_mode="HTML")

# === PTB FALLBACKS (for your modules safety) ===
async def ptb_message_counter(update, context):
    await pyro_message_counter(None, update.message)

async def ptb_seal(update, context):
    await pyro_seal(None, update.message)

async def ptb_msgcount(update, context):
    await pyro_msgcount(None, update.message)

# Add to YOUR application
application.add_handler(CommandHandler("seal", ptb_seal))
application.add_handler(CommandHandler("messagecount", ptb_msgcount))
application.add_handler(MessageHandler(
    (ptb_filters.TEXT | ptb_filters.PHOTO | ptb_filters.VIDEO | ptb_filters.STICKER)
    & ~ptb_filters.COMMAND & ptb_filters.ChatType.GROUPS,
    ptb_message_counter
))

# === Module Loader (YOUR existing modules) ===
for module_name in ALL_MODULES:
    try:
        importlib.import_module("Grabber.modules." + module_name)
        LOGGER.info(f"✅ Loaded module: {module_name}")
    except Exception as e:
        LOGGER.warning(f"⚠ Module load failed {module_name}: {e}")

# === MAIN (Drop-in replacement) ===
async def main():
    """Initialize waifu game + start everything."""
    # Waifu game init
    await load_message_counts()
    await preload_characters()
    LOGGER.info("🚀 Waifu game ready! Cache + counters loaded")
    
    # Start YOUR Pyrogram client
    await Grabberu.start()
    
    # Start YOUR PTB application
    ptb_task = asyncio.create_task(application.run_polling(drop_pending_updates=True))
    
    LOGGER.info("🔥 Grabber Bot LIVE!")
    LOGGER.info("✅ Pyrogram: Fast waifu spawns + /seal")
    LOGGER.info("✅ PTB: All your existing modules")
    
    # Idle (keeps everything running)
    await idle()
    
    # Cleanup
    ptb_task.cancel()
    await Grabberu.stop()

if __name__ == "__main__":
    asyncio.run(main())
