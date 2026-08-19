from pyrogram import filters, types, enums
from backend import app
from backend.database import user_collection
from backend.core.user import add_user_set_on_insert
from backend.core.utils import get_user_id_query, normalize_user_id, handle_errors
from backend.modules.collection.rarities import RARITY_MAP

@app.on_message(filters.command("hmode"))
@handle_errors
async def hmode_command(_, message: types.Message):
    user_id = message.from_user.id
    user = await user_collection.find_one(get_user_id_query(normalize_user_id(user_id)))
    current_mode = user.get('harem_mode', 'all') if user else 'all'
    
    markup = gen_hmode_keyboard(user_id, current_mode)
        
    await message.reply_text(
        "<b>Select Harem Display Mode:</b>\n\n"
        "Choose 'Default' to see all characters, or select a specific rarity to filter your /harem.\n\n"
        f"<b>Current Mode:</b> <code>{current_mode}</code>\n\n"
        "<i>Only you can use these buttons.</i>",
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML
    )

def gen_hmode_keyboard(user_id: int, current_mode: str):
    keyboard = []
    
    # Default button
    default_text = "✅ Default (All)" if current_mode == 'all' else "Default (All)"
    keyboard.append([types.InlineKeyboardButton(default_text, callback_data=f"set_hmode:all:{user_id}")])
    
    # Rarity buttons
    rarities = list(RARITY_MAP.values())
    for i in range(0, len(rarities), 2):
        row = []
        r1 = rarities[i]
        t1 = f"✅ {r1}" if current_mode == r1 else r1
        row.append(types.InlineKeyboardButton(t1, callback_data=f"set_hmode:{r1}:{user_id}"))
        
        if i + 1 < len(rarities):
            r2 = rarities[i+1]
            t2 = f"✅ {r2}" if current_mode == r2 else r2
            row.append(types.InlineKeyboardButton(t2, callback_data=f"set_hmode:{r2}:{user_id}"))
        keyboard.append(row)
    
    return types.InlineKeyboardMarkup(keyboard)

@app.on_callback_query(filters.regex(r"^set_hmode:"))
@handle_errors
async def set_hmode_callback(_, query: types.CallbackQuery):
    data = query.data.split(":")
    mode = data[1]
    owner_id = int(data[2])
    
    if query.from_user.id != owner_id:
        return await query.answer("❌ This menu is not for you!", show_alert=True)
    
    await user_collection.update_one(
        get_user_id_query(normalize_user_id(owner_id)),
        add_user_set_on_insert({"$set": {"harem_mode": mode}}, owner_id),
        upsert=True
    )
    
    await query.answer(f"Harem mode set to: {mode}")
    
    # Update the keyboard to show the new selection
    markup = gen_hmode_keyboard(owner_id, mode)
    await query.message.edit_text(
        "<b>Select Harem Display Mode:</b>\n\n"
        "Choose 'Default' to see all characters, or select a specific rarity to filter your /harem.\n\n"
        f"<b>Current Mode:</b> <code>{mode}</code>\n\n"
        "<i>Only you can use these buttons.</i>",
        reply_markup=markup,
        parse_mode=enums.ParseMode.HTML
    )
