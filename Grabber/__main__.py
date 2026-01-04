#!/usr/bin/env python3
"""
🔥 Main Grabber Bot - Pyrogram(app) + PTB(application) Hybrid 🔥
Updated from your FIRST file + enhanced economy module.
"""

import importlib
import asyncio
import random
import time
from html import escape
from typing import Dict, List

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import (
    CommandHandler, MessageHandler, filters as ptb_filters, CallbackContext, Update
)

# === YOUR ORIGINAL IMPORTS (EXACT from first file) ===
from Grabber import (
    collection, db, user_collection, message_counts_collection,
    application, LOGGER, user_totals_collection, Grabberu  # app = Grabberu
)
from Grabber.modules import ALL_MODULES

# Constants (from your first file)
SPECIAL_GROUP_ID = -1002528887253
ROYAL_NOTIFY_USER_ID = 7717913705

# Economy constants (from your economy module)
SUPPORT_GROUP_ID = -1002429397912
OWNER_ID = 6574393060
MAX_ACTIVE_GAMES = 100
WEEKLY_INTERVAL = 7

# === Globals ===
locks: Dict[str, asyncio.Lock] = {}
message_counts: Dict[str, int] = {}
waifu_spawn_order: Dict[str, int] = {}
last_characters: Dict[int, Dict] = {}
first_correct_guesses: Dict[int, int | None] = {}
warned_users: Dict[tuple[int, int], float] = {}
rarity_char_cache: Dict[str, List[Dict]] = {}
current_characters: Dict[int, Dict] = {}  # Economy nguess games

rarity_spawn_order = ["⚪ Common", "🟢 Medium", "🟠 Rare", "🟡 Legendary"]
special_rarity_thresholds = {"💠 Cosmic": 300, "💮 Exclusive": 600, "🔮 Limited Edition": 900, "🫧 Royal": 1000}

# === Utils ===
def normalize_tokens(text: str) -> List[str]:
    return [t for t in text.lower().split() if t]

def normalize_guess(guess: str) -> set:
    return {word for word in guess.lower().split() if len(word) > 1}

async def add_coins(user_id: int, amount: int) -> bool:
    if amount <= 0: return False
    result = await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}}, upsert=True)
    return bool(result.modified_count or result.upserted_id)

async def get_balance(user_id: int) -> int:
    user = await user_collection.find_one({"id": user_id}, {"balance": 1})
    return user.get("balance", 0) if user else 0

# === Waifu Game Preload ===
async def preload_characters():
    global rarity_char_cache
    rarity_char_cache.clear()
    cursor = collection.find({})
    async for doc in cursor:
        rarity_char_cache.setdefault(doc.get("rarity", ""), []).append(doc)
    LOGGER.info(f"Waifu cache: {len(rarity_char_cache)} rarities")

async def load_message_counts():
    global message_counts
    cursor = message_counts_collection.find({})
    async for doc in cursor:
        message_counts[str(doc["chat_id"])] = doc["count"]

async def save_message_counts():
    for chat_id, count in message_counts.items():
        await message_counts_collection.update_one({"chat_id": chat_id}, {"$set": {"count": count}}, upsert=True)

# === PYROGRAM WAIFU GAME (app = Grabberu) ===
@Grabberu.on_message((filters.text | filters.photo | filters.video | filters.sticker) & ~filters.command(None) & filters.group)
async def pyro_message_counter(client, message: Message):
    chat_id_int = message.chat.id
    chat_id = str(chat_id_int)
    
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    async with locks[chat_id]:
        count = message_counts.get(chat_id, 0)
        if count == 0:
            data = await message_counts_collection.find_one({"chat_id": chat_id})
            count = data["count"] if data else 0
        count += 1
        message_counts[chat_id] = count

        settings = await user_totals_collection.find_one({"chat_id": chat_id}) or {}
        freq = settings.get("message_frequency", 100)

        spawned = False
        for rarity, thresh in special_rarity_thresholds.items():
            if count % thresh == 0:
                if rarity == "🫧 Royal" and chat_id_int != SPECIAL_GROUP_ID:
                    continue
                await send_waifu(client, message, rarity)
                spawned = True
                break
        
        if not spawned and count % freq == 0:
            idx = waifu_spawn_order.get(chat_id, 0) % len(rarity_spawn_order)
            rarity = rarity_spawn_order[idx]
            waifu_spawn_order[chat_id] = idx + 1
            await send_waifu(client, message, rarity)
        
        if count % 200 == 0:
            await save_message_counts()

async def send_waifu(client, message: Message, rarity: str):
    chat_id = message.chat.id
    
    chars = rarity_char_cache.get(rarity) or await collection.find({"rarity": rarity}).to_list(None)
    if not chars: return
    
    grabber = first_correct_guesses.get(chat_id)
    if grabber:
        user = await user_collection.find_one({"id": grabber})
        name = user.get("first_name", "Unknown") if user else "Unknown"
        await client.send_message(chat_id, f'⚠ Already grabbed by <a href="tg://user?id={grabber}">{escape(name)}</a>', parse_mode="HTML")

    char = random.choice(chars)
    last_characters[chat_id] = char
    first_correct_guesses[chat_id] = None

    caption = "🪽 **New Waifu!**\n🦋 `/seal name` to claim!\n👑 Rarity revealed!"
    try:
        await client.send_photo(chat_id, char["img_url"], caption=caption, parse_mode="HTML")
    except Exception as e:
        LOGGER.error(f"Waifu send failed: {e}")

    if rarity == "🫧 Royal":
        await client.send_message(ROYAL_NOTIFY_USER_ID, f"👑 ROYAL in {chat_id}! ID: {char.get('id')}")

@Grabberu.on_message(filters.command("seal"))
async def pyro_seal(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    char = last_characters.get(chat_id)
    if not char: return
    
    if first_correct_guesses.get(chat_id):
        grabber = first_correct_guesses[chat_id]
        user = await user_collection.find_one({"id": grabber})
        name = user.get("first_name", "Unknown") if user else "Unknown"
        await message.reply(f'⚠ Already by <a href="tg://user?id={grabber}">{escape(name)}</a>', parse_mode="HTML")
        return
    
    now = time.time()
    key = (chat_id, user_id)
    if warned_users.get(key, 0) > now - 1: return
    warned_users[key] = now
    
    guess = " ".join(message.command[1:])
    g_tokens = normalize_tokens(guess)
    c_tokens = normalize_tokens(char["name"])
    
    if len(g_tokens) == len(c_tokens) and sorted(g_tokens) == sorted(c_tokens):
        first_correct_guesses[chat_id] = user_id
        await user_collection.update_one({"id": user_id}, {"$push": {"characters": char}}, upsert=True)
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Harem", switch_inline_query_current_chat=f"collection.{user_id}")]])
        await message.reply(
            f"💫 **{escape(message.from_user.first_name)} grabbed!**\n"
            f"🎗 **{escape(char['name'])}**\n🏵 **{escape(char['anime'])}**\n🎮 **{escape(char['rarity'])}**",
            parse_mode="HTML", reply_markup=kb
        )
    else:
        await message.reply("❌ Wrong name!")

@Grabberu.on_message(filters.command("messagecount"))
async def pyro_msgcount(client, message: Message):
    chat_id = str(message.chat.id)
    count = message_counts.get(chat_id, 0)
    if count == 0:
        data = await message_counts_collection.find_one({"chat_id": chat_id})
        count = data["count"] if data else 0
    await message.reply(f"📨 **Messages:** `{count:,}`", parse_mode="Markdown")

# === ECONOMY MODULE (Pyrogram - replaces your PTB economy) ===
@Grabberu.on_message(filters.command("balance", prefixes=["/", "!", "."]))
async def balance_cmd(client, message: Message):
    balance = await get_balance(message.from_user.id)
    await message.reply(f"💵 **Balance:** `{balance:,}` coins", parse_mode="Markdown")

@Grabberu.on_message(filters.command("pay") & filters.reply)
async def pay_cmd(client, message: Message):
    sender_id = message.from_user.id
    try:
        amount = int(message.command[1])
    except:
        await message.reply("❌ `/pay <amount>` (reply)")
        return
    
    recip_id = message.reply_to_message.from_user.id
    sender_bal = await get_balance(sender_id)
    
    if sender_bal < amount or sender_id == recip_id:
        await message.reply("❌ Invalid!")
        return
    
    await user_collection.update_one({"id": sender_id}, {"$inc": {"balance": -amount}})
    await user_collection.update_one({"id": recip_id}, {"$inc": {"balance": amount}})
    
    new_bal = await get_balance(sender_id)
    await message.reply(f"✅ **Paid `{amount:,}`**\n💵 **Balance:** `{new_bal:,}`", parse_mode="Markdown")

# === PTB FALLBACKS (your other modules safe) ===
async def ptb_seal(update: Update, context: CallbackContext): pass  # Handled by pyrogram
async def ptb_msgcount(update: Update, context: CallbackContext): pass

application.add_handler(CommandHandler("seal", ptb_seal))
application.add_handler(CommandHandler("messagecount", ptb_msgcount))

# === LOAD MODULES ===
for module_name in ALL_MODULES:
    importlib.import_module("Grabber.modules." + module_name)

# === MAIN (your original structure) ===
async def main():
    await load_message_counts()
    await preload_characters()
    
    await Grabberu.start()
    ptb_task = asyncio.create_task(application.run_polling(drop_pending_updates=True))
    
    LOGGER.info("🔥 Grabber LIVE - Pyrogram + PTB!")
    await asyncio.Event().wait()  # Idle equivalent
    
    ptb_task.cancel()
    await Grabberu.stop()

if __name__ == "__main__":
    asyncio.run(main())
