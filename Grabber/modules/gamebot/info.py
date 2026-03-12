from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import game_bot, BOT_USERNAME
from config import config

@game_bot.on_message(filters.command(["start", "help"]))
async def gamebot_start_handler(_, message: types.Message):
    """Dedicated /start and /help handler for GameBot."""
    main_bot_mention = f"@{BOT_USERNAME}" if BOT_USERNAME else "our main bot"
    
    text = (
        "<b>🎮 Welcome to the GameBot!</b>\n\n"
        f"I am the secondary assistant for {main_bot_mention}, dedicated to providing fun and interactive mini-games. "
        "Earn <b>Shards</b> and test your knowledge!\n\n"
        "<b>Available Commands:</b>\n"
        "🔹 <code>/nguess</code> - Start an anime character name guessing game\n"
        "🔹 <code>/quiz</code> - Test your anime knowledge and win Shards!\n\n"
        f"<i>Check out {main_bot_mention} for the full Seal-Bot experience!</i>"
    )
    
    buttons = [
        [
            types.InlineKeyboardButton("🛠 Support Group", url=f"https://t.me/{config.SUPPORT_CHAT}", style=enums.ButtonStyle.PRIMARY),
            types.InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{config.UPDATE_CHAT}", style=enums.ButtonStyle.PRIMARY)
        ],
        [
            types.InlineKeyboardButton("🤖 Visit Main Bot", url=f"https://t.me/{BOT_USERNAME}", style=enums.ButtonStyle.SUCCESS) if BOT_USERNAME else None
        ]
    ]
    # Filter out None buttons
    buttons = [[b for b in row if b] for row in buttons]
    
    await message.reply_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )
