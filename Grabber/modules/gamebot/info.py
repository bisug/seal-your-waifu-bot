from pyrogram import enums, filters, types

from config import config
from Grabber import game_bot
@game_bot.on_message(filters.command(["start", "help"]))
async def gamebot_start_handler(_, message: types.Message):
    """Dedicated /start and /help handler for GameBot."""
    main_bot_username = config.BOT_USERNAME
    main_bot_mention = f"@{main_bot_username}" if main_bot_username else "our main bot"
    text = (
        "<b>🎮 Welcome to the GameBot!</b>\n\n"
        f"I am the secondary assistant for {main_bot_mention}, dedicated to providing fun and interactive mini-games. "
        "Earn <b>Shards</b> and test your knowledge!\n\n"
        "<b>Available Commands:</b>\n"
        "🔹 <code>/nguess</code> - Identify a character from their image\n"
        "🔹 <code>/quiz</code> - Test your anime knowledge for Shards\n"
        "🔹 <code>/scramble</code> - Unscramble the shuffled character name\n"
        "🔹 <code>/top</code> - View GameBot rankings and totals\n\n"
        f"<i>Check out {main_bot_mention} for the full Seal-Bot experience!</i>"
    )
    buttons = [
        [
            types.InlineKeyboardButton("🛠 Support Group", url=f"https://t.me/{config.SUPPORT_CHAT}", style=enums.ButtonStyle.PRIMARY),
            types.InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{config.UPDATE_CHAT}", style=enums.ButtonStyle.PRIMARY)
        ],
        [
            types.InlineKeyboardButton("🤖 Visit Main Bot", url=f"https://t.me/{main_bot_username}", style=enums.ButtonStyle.SUCCESS) if main_bot_username else None
        ]
    ]
    # Filter out None buttons
    buttons = [[b for b in row if b] for row in buttons]
    await game_bot.send_message_safe(
        message.chat.id,
        text,
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=types.ReplyParameters(message_id=message.id)
    )
