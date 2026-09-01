import html
import random
import uuid
from datetime import timedelta, timezone

import httpx
from pymongo import ReturnDocument
from pyrogram import enums, filters, types

from backend.client import game_bot
from backend.core.logging import get_logger
from backend.core.utils import get_now_utc, html_escape
from backend.database import quiz_questions_collection, sessions_collection
from backend.modules.gamebot.common import award_gamebot_shards, ensure_gamebot_ready

LOGGER = get_logger(__name__)
QUIZ_API_URL = "https://opentdb.com/api.php?amount=1&category=31"
QUIZ_REWARD = 250
QUIZ_TTL = timedelta(seconds=30)
@game_bot.on_message(filters.command("quiz"))
async def quiz_cmd(_, message: types.Message):
    if not await ensure_gamebot_ready(message):
        return
    user_id = message.from_user.id
    try:
        result = None
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(QUIZ_API_URL, timeout=10)
                data = response.json()
                if data.get("response_code") == 0:
                    result = data["results"][0]
            except Exception as e:
                LOGGER.warning(f"Quiz API failed, falling back to DB: {e}")
        if not result:
            cursor = await quiz_questions_collection.aggregate([{"$sample": {"size": 1}}])
            questions = await cursor.to_list(length=1)
            if questions:
                result = questions[0]
            else:
                return await game_bot.send_message_safe(message.chat.id, "❌ <b>Failed to fetch a quiz question and no cache available.</b>", parse_mode=enums.ParseMode.HTML)
        else:
            await quiz_questions_collection.update_one(
                {"question": result["question"]},
                {"$set": result},
                upsert=True
            )
        question = html_escape(html.unescape(result["question"]))
        correct_answer = html.unescape(result["correct_answer"]) # No escape here since it's for buttons or logic
        incorrect_answers = [html.unescape(ans) for ans in result["incorrect_answers"]]
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)
        correct_index = all_answers.index(correct_answer)
        nonce = uuid.uuid4().hex[:12]
        session_id = f"quiz:{nonce}"
        await sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "owner_id": user_id,
                    "chat_id": message.chat.id,
                    "correct_index": correct_index,
                    "answers": all_answers,
                    "question": question,
                    "claimed": False,
                    "expires_at_dt": get_now_utc() + QUIZ_TTL,
                }
            },
            upsert=True,
        )
        buttons = []
        row = []
        for i, ans in enumerate(all_answers):
            btn_data = f"qz:{nonce}:{i}"
            row.append(types.InlineKeyboardButton(ans, callback_data=btn_data))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        text = (
            f"🧠 <b>Quiz Time!</b>\n\n"
            f"<b>Question:</b> {question}\n\n"
            f"⏱ <i>You have 30 seconds to answer!</i>"
        )
        sent = await game_bot.send_message_safe(
            message.chat.id,
            text,
            reply_markup=types.InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
        if not sent:
            await sessions_collection.delete_one({"_id": session_id})
    except Exception as e:
        LOGGER.error(f"Quiz Error: {e}")
        await game_bot.send_message_safe(message.chat.id, "❌ <b>An error occurred while starting the quiz.</b>", parse_mode=enums.ParseMode.HTML)
@game_bot.on_callback_query(filters.regex(r"^qz:"))
async def quiz_callback_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    if len(data) != 3:
        return await query.answer("This quiz has expired.", show_alert=True)
    nonce = data[1]
    pressed_idx = int(data[2])
    session_id = f"quiz:{nonce}"
    session = await sessions_collection.find_one({"_id": session_id})
    if not session:
        return await query.answer("This quiz has expired or was already answered.", show_alert=True)
    user_id = int(session.get("owner_id", 0))
    if query.from_user.id != user_id:
        return await query.answer("❌ This quiz is not for you!", show_alert=True)
    now = get_now_utc()
    expires_at = session.get("expires_at_dt")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at <= now:
        await game_bot.edit_message_text_safe(query.message.chat.id, query.message.id, "⏱ <b>Time's up!</b> The quiz has expired.", parse_mode=enums.ParseMode.HTML)
        await sessions_collection.delete_one({"_id": session_id})
        return await query.answer("Too late!")
    claimed = await sessions_collection.find_one_and_update(
        {
            "_id": session_id,
            "owner_id": user_id,
            "claimed": {"$ne": True},
            "expires_at_dt": {"$gt": now},
        },
        {
            "$set": {
                "claimed": True,
                "pressed_idx": pressed_idx,
                "answered_at_dt": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        return await query.answer("This quiz was already answered.", show_alert=True)
    correct_idx = int(claimed["correct_index"])
    if pressed_idx == correct_idx:
        updated_user = await award_gamebot_shards(
            query.from_user,
            QUIZ_REWARD,
            extra_inc={"quiz_count": 1},
            game_key="quiz",
        )
        new_balance = int(updated_user.get("balance", 0) or 0)
        result_text = (
            f"✅ <b>Correct!</b>\n\n"
            f"💰 <b>Reward:</b> {QUIZ_REWARD} Shards\n"
            f"💳 <b>New Balance:</b> {new_balance:,} Shards\n\n"
            "Well done! 🎉"
        )
    else:
        answers = claimed.get("answers", [])
        correct_answer_text = answers[correct_idx] if 0 <= correct_idx < len(answers) else "Unknown"
        result_text = f"❌ <b>Wrong!</b>\n\nThe correct answer was: <b>{html_escape(correct_answer_text)}</b>"
    await sessions_collection.delete_one({"_id": session_id})
    await game_bot.edit_message_text_safe(
        query.message.chat.id,
        query.message.id,
        f"{query.message.text.split('⏱')[0]}\n\n{result_text}",
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer()
