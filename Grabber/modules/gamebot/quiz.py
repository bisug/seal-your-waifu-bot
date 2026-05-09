import html
import random
import time
import httpx
from pyrogram import enums, errors, filters, types
from Grabber import LOGGER, app, game_bot, quiz_questions_collection
from Grabber.core.balance import get_user_balance, update_user_balance
from Grabber.core.utils import check_member_requirement, html_escape
QUIZ_API_URL = "https://opentdb.com/api.php?amount=1&category=31"
@game_bot.on_message(filters.command("quiz"))
async def quiz_cmd(_, message: types.Message):
    meets_req, reason, count = await check_member_requirement(game_bot, message.chat)
    if not meets_req:
        if reason == "group_only":
            text = "❌ <b>Group Required:</b> This game can only be played in group chats."
        elif reason == "member_count":
            text = (
                f"⚠️ <b>Security Level Low:</b> This sector must contain at least <b>50 personnel</b> (members) to authorize GameBot operations.\n\n"
                f"Current count: <code>{count}</code>"
            )
        else: # main_bot_missing
            from Grabber import BOT_NAME, BOT_USERNAME
            text = (
                f"🚫 <b>Main Bot Missing:</b> GameBot operations require the presence of <b>{BOT_NAME}</b> (@{BOT_USERNAME}) in this sector.\n\n"
                f"<i>Please add the Main Bot to authorize games!</i>"
            )
        return await game_bot.send_message_safe(message.chat.id, text, auto_delete=300)
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
        timestamp = int(time.time())
        buttons = []
        row = []
        for i, ans in enumerate(all_answers):
            callback_data = f"quiz:{correct_index}:{user_id}:{timestamp}"
            if i == correct_index:
                pass
            btn_data = f"qz:{i}:{correct_index}:{user_id}:{timestamp}"
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
        await game_bot.send_message_safe(
            message.chat.id,
            text,
            reply_markup=types.InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Quiz Error: {e}")
        await game_bot.send_message_safe(message.chat.id, "❌ <b>An error occurred while starting the quiz.</b>", parse_mode=enums.ParseMode.HTML)
@game_bot.on_callback_query(filters.regex(r"^qz:"))
async def quiz_callback_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    pressed_idx = int(data[1])
    correct_idx = int(data[2])
    user_id = int(data[3])
    timestamp = int(data[4])
    if query.from_user.id != user_id:
        return await query.answer("❌ This quiz is not for you!", show_alert=True)
    if time.time() - timestamp > 30:
        await game_bot.edit_message_text_safe(query.message.chat.id, query.message.id, "⏱ <b>Time's up!</b> The quiz has expired.", parse_mode=enums.ParseMode.HTML)
        return await query.answer("Too late!")
    if pressed_idx == correct_idx:
        await update_user_balance(user_id, 100)
        new_balance = await get_user_balance(user_id)
        result_text = (
            f"✅ <b>Correct!</b>\n\n"
            f"💰 <b>Reward:</b> 100 Shards\n"
            f"💳 <b>New Balance:</b> {new_balance:,} Shards\n\n"
            "Well done! 🎉"
        )
    else:
        correct_answer_text = "Unknown"
        for row in query.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data.split(":")[1] == str(correct_idx):
                    correct_answer_text = btn.text
                    break
        result_text = f"❌ <b>Wrong!</b>\n\nThe correct answer was: <b>{html_escape(correct_answer_text)}</b>"
    await game_bot.edit_message_text_safe(
        query.message.chat.id,
        query.message.id,
        f"{query.message.text.split('⏱')[0]}\n\n{result_text}",
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer()
