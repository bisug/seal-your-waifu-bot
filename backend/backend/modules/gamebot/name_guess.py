from datetime import timedelta
import re
from pymongo import ReturnDocument
from pyrogram import filters, types
from backend import collection, game_bot, sessions_collection
from backend.core.tasks import run_background_task
from backend.core.utils import get_now_utc, html_escape
from backend.modules.gamebot.common import (
    award_gamebot_shards,
    ensure_gamebot_ready,
    ensure_registered_user,
)
# Local cache is no longer used for character data to ensure persistence
# Active sessions are stored in sessions_collection with ID: "nguess:{chat_id}"
NGUESS_TTL = timedelta(minutes=5)
NAME_GUESS_BASE_REWARD = 125
NAME_GUESS_PLAYER_BONUS = 25
NAME_GUESS_MAX_REWARD = 300
NAME_GUESS_MID_MILESTONE_BONUS = 1_500
NAME_GUESS_ELITE_MILESTONE_BONUS = 3_000
# Send message safe is now handled by game_bot.send_message_safe and game_bot.send_media_safe
async def start_nguess_game(chat_id):
    """Fetches a character and starts a new game session."""
    # Fetch a random character
    cursor = await collection.aggregate([{"$sample": {"size": 1}}])
    res = await cursor.to_list(length=1)
    if not res:
        return await game_bot.send_message_safe(chat_id, text=html_escape("DATABASE ERROR: No target profiles available."), auto_delete=300)
    char = res[0]
    # Create/Update session in DB
    await sessions_collection.update_one(
        {"_id": f"nguess:{chat_id}"},
        {
            "$set": {
                "char": char,
                "players": [],
                "expires_at_dt": get_now_utc() + NGUESS_TTL,
            },
            "$unset": {
                "winner_id": "",
                "answered_at_dt": "",
            },
        },
        upsert=True
    )
    anime_name = char['anime']
    briefing = f"Identify this character from the series <b>{html_escape(anime_name)}</b>"
    sent = await game_bot.send_media_safe(
        chat_id,
        media_url=char['img_url'],
        caption=briefing,
        auto_delete=300
    )
    if not sent:
        await sessions_collection.delete_one({"_id": f"nguess:{chat_id}"})
        await game_bot.send_message_safe(chat_id, text=html_escape("CRITICAL FAILURE: Transponder link lost."), auto_delete=300)
def get_name_variants(name: str):
    """Generates possible name variants for matching."""
    name = name.lower().strip()
    parts = re.split(r'\s+', name)
    variants = {name}
    for part in parts:
        if len(part) > 2:
            variants.add(part)
    return variants
@game_bot.on_message(filters.command("nguess"))
async def nguess_start_handler(_, message: types.Message):
    chat_id = message.chat.id
    if not await ensure_gamebot_ready(message):
        return
    # If a game is active, we just proceed to start a new one (per user request: "send next instead")
    await start_nguess_game(chat_id)
@game_bot.on_message(filters.text & filters.group & ~filters.command(["nguess", "top", "ctop"]), group=10)
async def nguess_check_handler(_, message: types.Message):
    if not message.from_user or not message.text or message.text.startswith("/"):
        return
    chat_id = message.chat.id
    now = get_now_utc()
    session = await sessions_collection.find_one(
        {
            "_id": f"nguess:{chat_id}",
            "$or": [
                {"expires_at_dt": {"$exists": False}},
                {"expires_at_dt": {"$gt": now}},
            ],
            "$and": [
                {
                    "$or": [
                        {"winner_id": {"$exists": False}},
                        {"winner_id": None},
                    ]
                }
            ],
        }
    )
    if not session:
        return
    guess = message.text.lower().strip()
    char = session["char"]
    name_variants = get_name_variants(char['name'])
    if guess in name_variants:
        # Check registration before rewarding
        if not await ensure_registered_user(message.from_user, chat_id):
            return

        claim_filter = {
            "_id": f"nguess:{chat_id}",
            "$or": [
                {"expires_at_dt": {"$exists": False}},
                {"expires_at_dt": {"$gt": now}},
            ],
            "$and": [
                {
                    "$or": [
                        {"winner_id": {"$exists": False}},
                        {"winner_id": None},
                    ]
                }
            ],
        }
        if char.get("id") is not None:
            claim_filter["char.id"] = char.get("id")
        else:
            claim_filter["char.name"] = char.get("name")

        claimed = await sessions_collection.find_one_and_update(
            claim_filter,
            {
                "$set": {
                    "winner_id": message.from_user.id,
                    "answered_at_dt": now,
                },
                "$addToSet": {"players": message.from_user.id},
            },
            return_document=ReturnDocument.AFTER,
        )
        if not claimed:
            return

        # Correct guess!
        player_count = len(claimed.get("players", []))
        reward = min(
            NAME_GUESS_BASE_REWARD + (player_count - 1) * NAME_GUESS_PLAYER_BONUS,
            NAME_GUESS_MAX_REWARD,
        )
        # Increment global counter
        stats = await sessions_collection.find_one_and_update(
            {"id": "nguess_global_stats"},
            {"$inc": {"total_guesses": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        total_guesses = stats.get("total_guesses", 1)
        bonus = 0
        milestone_text = ""
        if total_guesses % 100 == 0:
            bonus = NAME_GUESS_ELITE_MILESTONE_BONUS
            milestone_text = f"\n\n<b>ELITE MILESTONE ACHIEVED</b>\nYou are the 100th guesser! Granted {bonus:,} bonus Shards."
        elif total_guesses % 100 == 50:
            bonus = NAME_GUESS_MID_MILESTONE_BONUS
            milestone_text = f"\n\n<b>MILESTONE REACHED</b>\nYou are the 50th guesser! Granted {bonus:,} bonus Shards."
        total_reward = reward + bonus
        await award_gamebot_shards(
            message.from_user,
            total_reward,
            extra_inc={"guess_count": 1},
            game_key="name_guess",
        )

        # Track Quests and Achievements
        from backend.modules.progression.quests import update_quest_progress
        from backend.modules.progression.achievements import check_achievements
        run_background_task(update_quest_progress(message.from_user.id, "guesser", 1))
        run_background_task(update_quest_progress(message.from_user.id, "weekly_guesser", 1))
        run_background_task(check_achievements(message.from_user.id))

        # Delete session
        await sessions_collection.delete_one({"_id": f"nguess:{chat_id}", "winner_id": message.from_user.id})
        display_progress = total_guesses % 100 if total_guesses % 100 != 0 else 100
        mention = f'<a href="tg://user?id={message.from_user.id}">{html_escape(message.from_user.first_name)}</a>'
        target_name = html_escape(char['name'])
        success_msg = (
            f"✅ {mention} identified <b>{target_name}</b>!\n"
            f"💰 <b>Bounty:</b> +{reward} Shards\n"
            f"🔥 <b>Progress:</b> {display_progress}/100{milestone_text}"
        )
        await game_bot.send_message_safe(chat_id, text=success_msg, auto_delete=300)
        # Recursive start
        await start_nguess_game(chat_id)
    else:
        await sessions_collection.update_one(
            {"_id": f"nguess:{chat_id}"},
            {"$addToSet": {"players": message.from_user.id}},
        )
