import time
import random
import datetime
from typing import Optional, Dict, Any
from pyrogram import enums
from Grabber.database import spawns_collection, message_counts_collection, user_totals_collection
from Grabber import app, LOGGER, config
from Grabber.core.waifu import get_or_load_characters

ROYAL_NOTIFY_USER_ID = config.ROYAL_NOTIFY_USER_ID
from typing import Optional, Dict, Any
from Grabber.database import spawns_collection, message_counts_collection, user_totals_collection

async def track_user_activity(chat_id: int, user_id: int):
                                                                    
    current_time = time.time()
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {f"active_users.{user_id}": current_time}},
        upsert=True
    )

async def get_active_user_count(chat_id: int) -> int:
                                                               
    state = await get_chat_state(chat_id)
    active_dict = state.get("active_users", {})
    current_time = time.time()
                                                          
    active_count = sum(1 for ts in active_dict.values() if ts > current_time - 600)
    return active_count

async def get_chat_state(chat_id: int) -> Dict[str, Any]:
                                                          
    state = await spawns_collection.find_one({"chat_id": chat_id})
    return state or {}

async def set_active_spawn(chat_id: int, character: Dict[str, Any], message_id: int):
                                          
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "last_character": character,
                "message_id": message_id,
                "first_correct_guess": None,
                "last_spawn_time": time.time()
            }
        },
        upsert=True
    )

async def clear_active_spawn(chat_id: int, user_id: int):
                                                            
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {
            "$set": {"first_correct_guess": user_id},
            "$unset": {"last_character": "", "message_id": ""}
        }
    )

async def get_message_count(chat_id: int) -> int:
    doc = await message_counts_collection.find_one({"chat_id": str(chat_id)})
    return doc["count"] if doc else 0

async def increment_message_count(chat_id: int) -> int:
                                                       
    res = await message_counts_collection.find_one_and_update(
        {"chat_id": str(chat_id)},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True
    )
    return res["count"]

async def get_spawn_order(chat_id: int) -> int:
    state = await get_chat_state(chat_id)
    return state.get("spawn_order", 0)

async def increment_spawn_order(chat_id: int):
    await spawns_collection.update_one(
        {"chat_id": chat_id},
        {"$inc": {"spawn_order": 1}},
        upsert=True
    )

async def get_chat_frequency(chat_id: int) -> int:
    doc = await user_totals_collection.find_one(
        {"chat_id": str(chat_id)},
        projection={"message_frequency": 1}
    )

                                                                              
async def send_character(chat_id: int, rarity: str):
    chars = await get_or_load_characters(rarity)
    if not chars:
        return

    character = random.choice(chars)

                       
    now = datetime.datetime.now(datetime.timezone.utc)
    golden_text = ""
    if 20 <= now.hour <= 22:
        golden_text = "\n🌟 **Golden Hour is Active!**"

    caption = (
        "🪽 **A new character appeared!**\n"
        "🦋 Use /seal <name> to collect them!\n"
        "👑 Rarity is secret until caught!"
        f"{golden_text}"
    )

    try:
        await app.send_chat_action(chat_id, enums.ChatAction.UPLOAD_PHOTO)
        msg = await app.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        await set_active_spawn(chat_id, character, msg.id)
        
    except Exception as e:
        LOGGER.error(f"Error sending character: {e}")

    if rarity == "🫧 Royal":
        try:
            await app.send_message(
                ROYAL_NOTIFY_USER_ID,
                f"👑 **Royal Spawn!**\nID: `{character['id']}`\nName: {character['name']}"
            )
        except Exception:
            pass
