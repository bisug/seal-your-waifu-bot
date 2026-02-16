import random
import time
import html
import httpx
from pyrogram import filters, types, enums
from Grabber.app import app
from Grabber import LOGGER

# ─── API URL ────────────────────────────────────────────────────────────────
QUIZ_API_URL = "https://opentdb.com/api.php?amount=1&category=31&difficulty=easy"

@app.on_message(filters.command("quiz"))
async def quiz_cmd(_, message: types.Message):
    user_id = message.from_user.id
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(QUIZ_API_URL, timeout=10)
            data = response.json()
            
        if data.get("response_code") != 0:
            return await message.reply_text("❌ **Failed to fetch a quiz question. Try again later.**")
            
        result = data["results"][0]
        question = html.unescape(result["question"])
        correct_answer = html.unescape(result["correct_answer"])
        incorrect_answers = [html.unescape(ans) for ans in result["incorrect_answers"]]
        
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)
        
        # We need to store the correct answer somewhere to verify it.
        # To avoid complex server-side state, we can include the correct answer's hash 
        # or index in the callback data, but user_id is better for security.
        # Callback data: quiz:<user_id>:<timestamp>:<correct_index>
        
        correct_index = all_answers.index(correct_answer)
        timestamp = int(time.time())
        
        buttons = []
        row = []
        for i, ans in enumerate(all_answers):
            # quiz:<correct_idx>:<user_id>:<timestamp>
            callback_data = f"quiz:{correct_index}:{user_id}:{timestamp}"
            if i == correct_index:
                # We'll handle checking by index in the callback
                pass
            
            # Since callback_data has a limit (64 bytes), we'll use a simpler format.
            # quiz:<user_idx_pressed>:<correct_idx>:<user_id>:<timestamp>
            btn_data = f"qz:{i}:{correct_index}:{user_id}:{timestamp}"
            row.append(types.InlineKeyboardButton(ans, callback_data=btn_data))
            
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
            
        text = (
            f"🧠 **Quiz Time!**\n\n"
            f"**Question:** {question}\n\n"
            f"⏱ _You have 30 seconds to answer!_"
        )
        
        await message.reply_text(
            text,
            reply_markup=types.InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.MARKDOWN
        )
        
    except Exception as e:
        LOGGER.error(f"Quiz Error: {e}")
        await message.reply_text("❌ **An error occurred while starting the quiz.**")

@app.on_callback_query(filters.regex(r"^qz:"))
async def quiz_callback_handler(_, query: types.CallbackQuery):
    data = query.data.split(":")
    # qz:<pressed_idx>:<correct_idx>:<user_id>:<timestamp>
    pressed_idx = int(data[1])
    correct_idx = int(data[2])
    user_id = int(data[3])
    timestamp = int(data[4])
    
    if query.from_user.id != user_id:
        return await query.answer("❌ This quiz is not for you!", show_alert=True)
        
    if time.time() - timestamp > 30:
        await query.message.edit_text("⏱ **Time's up!** The quiz has expired.")
        return await query.answer("Too late!")
        
    if pressed_idx == correct_idx:
        result_text = "✅ **Correct!** Well done! 🎉"
    else:
        # Get the correct answer text from the buttons
        correct_answer_text = "Unknown"
        for row in query.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data.split(":")[1] == str(correct_idx):
                    correct_answer_text = btn.text
                    break
        
        result_text = f"❌ **Wrong!**\n\nThe correct answer was: **{correct_answer_text}**"
        
    await query.message.edit_text(
        f"{query.message.text.split('⏱')[0]}\n\n{result_text}",
        parse_mode=enums.ParseMode.MARKDOWN
    )
    await query.answer()
