import random
from pyrogram import enums, filters, types

from Grabber import LOGGER, PHOTO_URL, app
from Grabber.core.eggs import get_incubating_count
from Grabber.core.pass_config import get_pass_incubation_slots
from Grabber.core.progression import get_progress_bar, get_user_progress
from Grabber.core.roles import get_role_payload
from Grabber.core.user import get_active_pet, get_user_data, get_user_rank_with_fallback
from Grabber.core.utils import handle_errors, html_escape, reply_media_dynamic
from Grabber.database import collection
RARITY_ICONS = {
    'Common': '◌', 'Medium': '○', 'Rare': '◙',
    'Legendary': '◎', 'Cosmic': '◉', 'Exclusive': '◈',
    'Limited Edition': '▣', 'Royal': '◆', 'Antique': '◇',
    'Celestial': '✦', 'AMV': '▰', 'Prestige': '✧',
}


def _unique_characters(characters: list) -> list[dict]:
    unique = {}
    for index, character in enumerate(characters):
        if not isinstance(character, dict):
            continue
        key = character.get("id")
        key = str(key) if key is not None else f"missing:{index}"
        unique.setdefault(key, character)
    return list(unique.values())


@app.on_message(filters.command(["profile", "myprofile", "me", "status", "mystatus"]))
@handle_errors
async def profile_handler(_, message: types.Message):
    """Generate and display the user's progress and collection profile."""
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        return await message.reply_text("<b>No profile found!</b> Try collecting a character first.", parse_mode=enums.ParseMode.HTML)
    await app.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    user_name = html_escape(message.from_user.first_name or "Collector")
    user_balance = user_data.get('balance', 0)
    zenith = user_data.get('zenith', 0)
    chars = user_data.get('characters', [])
    owned_copies = user_data.get('char_count')
    if owned_copies is None:
        owned_copies = len(chars)
    unique_chars = _unique_characters(chars)
    unique_count = len(unique_chars)
    total_db_chars = await collection.estimated_document_count()
    progress_percent = (unique_count / total_db_chars * 100) if total_db_chars > 0 else 0
    progress_percent = min(100, max(0, progress_percent))
    bar_len = 10
    filled = int(progress_percent / 100 * bar_len)
    progress_bar = "▰" * filled + "▱" * (bar_len - filled)
    progress = await get_user_progress(user_id, user_data=user_data)
    level = progress["level"]
    total_xp = progress["xp"]
    xp_current = progress["xp_current"]
    xp_needed = progress["xp_needed"]
    pass_type = progress["pass_type"].capitalize()
    xp_bar = get_progress_bar(xp_current, xp_needed, 10)
    rank, total_ranked, percentile = await get_user_rank_with_fallback(user_id, total_xp)
    role_payload = get_role_payload(user_id)
    active_pet = await get_active_pet(user_id)
    pet_text = html_escape(f"{active_pet['name']} (Lvl {active_pet.get('level', 1)})") if active_pet else "None"
    eggs = user_data.get("eggs") or []
    active_incubations = get_incubating_count(eggs)
    incubation_slots = get_pass_incubation_slots(user_data)
    titles = user_data.get("titles") or ["Rookie"]
    title = html_escape(str(user_data.get("title") or titles[-1] or "Rookie"))
    achievement_count = len(user_data.get("achievements") or [])
    favs = user_data.get('favorites', [])
    fav_id = favs[0] if favs else None
    fav_char = next((c for c in chars if isinstance(c, dict) and str(c.get('id')) == str(fav_id)), None)
    fav_name = html_escape(str(fav_char.get('name') or "None")) if fav_char else "None"
    rarity_stats = {}
    for c in unique_chars:
        r = c.get('rarity', '⚪ Common')
        rarity_stats[r] = rarity_stats.get(r, 0) + 1
    role_text = ""
    if role_payload.get("role_label"):
        role_text = (
            f"<b>Role:</b> {html_escape(role_payload.get('role_symbol') or '')} "
            f"{html_escape(role_payload['role_label'])}\n"
        )
    profile_text = (
        f"<b>Collector Profile</b>\n"
        f"<b>{user_name}</b> <code>{user_id}</code>\n\n"
        f"<b>Title:</b> <code>{title}</code>\n"
        f"<b>Rank:</b> <code>#{rank:,}</code> / <code>{total_ranked:,}</code> ({percentile:.1f}%)\n"
        f"{role_text}"
        f"<b>Battle Pass:</b> {pass_type}\n\n"
        f"<b>Level:</b> <code>{level}</code>\n"
        f"<b>XP:</b> {xp_bar} <code>{xp_current:,}/{xp_needed:,}</code>\n"
        f"<b>Total XP:</b> <code>{total_xp:,}</code>\n\n"
        f"<b>Wallet:</b> <code>{user_balance:,}</code> Shards | <code>{zenith:,}</code> Zenith\n\n"
        f"<b>Collection:</b> <code>{unique_count:,}/{total_db_chars:,}</code> unique ({progress_percent:.1f}%)\n"
        f"<b>Total Copies:</b> <code>{owned_copies:,}</code>\n"
        f"<b>Completion:</b> {progress_bar}\n"
        f"<b>Favorite:</b> <code>{fav_name}</code>\n"
        f"<b>Active Pet:</b> <code>{pet_text}</code>\n"
        f"<b>Incubation:</b> <code>{active_incubations}/{incubation_slots}</code> slots\n"
        f"<b>Achievements:</b> <code>{achievement_count}</code>\n\n"
        f"<b>Collection By Rarity</b>\n"
    )
    for rarity_key, symbol in RARITY_ICONS.items():
        count = 0
        for db_rarity, db_count in rarity_stats.items():
            if rarity_key in db_rarity:
                count += db_count
        profile_text += f"{html_escape(symbol)} {html_escape(rarity_key)}: <code>{count}</code>\n"
    from Grabber.core.keyboard import KeyboardBuilder, get_webapp_button
    is_private = message.chat.type == enums.ChatType.PRIVATE
    builder = KeyboardBuilder()
    builder.add_button("View Harem", callback_data=f"harem_view:{user_id}", style=enums.ButtonStyle.PRIMARY)
    webapp_btn = get_webapp_button(is_private, path="#profile")
    if webapp_btn:
        builder.add_row(webapp_btn)
    reply_markup = builder.build()
    try:
        pic = random.choice(PHOTO_URL)
        await reply_media_dynamic(message, pic,
            caption=profile_text,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Profile Photo Error: {e}")
        await message.reply_text(profile_text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
