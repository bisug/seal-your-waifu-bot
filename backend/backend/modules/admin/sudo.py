import math

from pyrogram import enums, filters, types

from backend import sudo_filter
from backend.client import app
from backend.core.logging import get_logger
from backend.core.roles import (
    MANAGED_ROLES,
    MODERATOR_ROLE,
    ROLE_META,
    ROLE_ORDER,
    format_role_benefits,
    format_upload_reward,
    normalize_role,
    sudo_roles,
    sudo_users,
)
from backend.core.utils import handle_errors, html_escape
from backend.database import sudo_collection
from config import config

LOGGER = get_logger(__name__)

SUDO_PAGE_SIZE = 6


def _role_help() -> str:
    return "Roles: <code>moderator</code> or <code>uploader</code>."


async def _set_sudo_role(target_id: int, role: str) -> dict:
    await sudo_collection.delete_many({"user_id": {"$in": [target_id, str(target_id)]}})
    await sudo_collection.insert_one({"user_id": target_id, "role": role})
    if role == MODERATOR_ROLE and target_id not in sudo_users:
        sudo_users.append(target_id)
    elif role != MODERATOR_ROLE and target_id in sudo_users:
        sudo_users.remove(target_id)
    sudo_roles[target_id] = role
    return ROLE_META[role]


async def _remove_sudo_role(target_id: int):
    res = await sudo_collection.delete_one({"user_id": {"$in": [target_id, str(target_id)]}})
    if target_id in sudo_users:
        sudo_users.remove(target_id)
    sudo_roles.pop(target_id, None)
    return res


async def _get_sudo_records() -> list[dict]:
    records = [{"user_id": config.OWNER_ID, "role": "owner", "is_owner": True}]
    seen = {config.OWNER_ID}
    cursor = sudo_collection.find({})
    sudos = await cursor.to_list(length=None)
    for sudo in sudos:
        try:
            user_id = int(sudo.get("user_id"))
        except (TypeError, ValueError):
            continue
        if user_id in seen:
            continue
        role = normalize_role(sudo.get("role")) or MODERATOR_ROLE
        records.append({"user_id": user_id, "role": role, "is_owner": False})
        seen.add(user_id)

    return sorted(records, key=lambda item: (-ROLE_ORDER[item["role"]], item["user_id"]))


async def _get_user_label(user_id: int) -> str:
    try:
        user = await app.get_users(user_id)
        return html_escape(user.first_name or user.username or f"User {user_id}")
    except Exception:
        return f"User {user_id}"


def _role_line(role: str) -> str:
    meta = ROLE_META[role]
    reward = format_upload_reward(meta.get("upload_reward"))
    bits = [
        f"<b>Role:</b> {html_escape(meta['label'])} <code>{meta['symbol']} {meta['tag']}</code>",
        f"<b>Upload:</b> <code>{'Yes' if meta['can_upload'] else 'No'}</code>",
        f"<b>Edit:</b> <code>{'Yes' if meta['can_edit_character'] else 'No'}</code>",
    ]
    if reward:
        bits.append(f"<b>Upload reward:</b> <code>{html_escape(reward)}</code>")
    benefits = format_role_benefits(meta.get("perks"))
    if benefits:
        bits.append(f"<b>Benefits:</b> <code>{html_escape(', '.join(benefits))}</code>")
    return "\n".join(bits)


async def _build_sudo_list_page(viewer_id: int, page: int = 0):
    records = await _get_sudo_records()
    total_pages = max(1, math.ceil(len(records) / SUDO_PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))
    start = page * SUDO_PAGE_SIZE
    page_records = records[start:start + SUDO_PAGE_SIZE]

    text = (
        "👤 <b>Sudo Roles</b>\n\n"
        f"Page <code>{page + 1}</code>/<code>{total_pages}</code>\n"
        "Select a staff member below."
    )
    keyboard = []
    for record in page_records:
        user_id = record["user_id"]
        meta = ROLE_META[record["role"]]
        label = await _get_user_label(user_id)
        keyboard.append([
            types.InlineKeyboardButton(
                f"{meta['symbol']} {meta['tag']} · {label}",
                callback_data=f"sudo_view:{viewer_id}:{page}:{user_id}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("‹ Prev", callback_data=f"sudo_page:{viewer_id}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(types.InlineKeyboardButton("Next ›", callback_data=f"sudo_page:{viewer_id}:{page + 1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append([types.InlineKeyboardButton("Close", callback_data=f"sudo_close:{viewer_id}")])
    return text, types.InlineKeyboardMarkup(keyboard)


async def _build_sudo_detail(viewer_id: int, page: int, target_id: int):
    if target_id == config.OWNER_ID:
        role = "owner"
        is_owner = True
    else:
        doc = await sudo_collection.find_one({"user_id": {"$in": [target_id, str(target_id)]}})
        if not doc:
            role = None
            is_owner = False
        else:
            role = normalize_role(doc.get("role")) or MODERATOR_ROLE
            is_owner = False

    if not role:
        text = f"❌ User <code>{target_id}</code> is not in the sudo list."
        keyboard = [[types.InlineKeyboardButton("Back", callback_data=f"sudo_page:{viewer_id}:{page}")]]
        return text, types.InlineKeyboardMarkup(keyboard)

    label = await _get_user_label(target_id)
    text = (
        f"👤 <b>{label}</b>\n"
        f"<b>ID:</b> <code>{target_id}</code>\n\n"
        f"{_role_line(role)}"
    )
    keyboard = []
    if viewer_id == config.OWNER_ID and not is_owner:
        keyboard.append([
            types.InlineKeyboardButton("Set Moderator", callback_data=f"sudo_role:{viewer_id}:{page}:{target_id}:moderator"),
            types.InlineKeyboardButton("Set Uploader", callback_data=f"sudo_role:{viewer_id}:{page}:{target_id}:uploader"),
        ])
        keyboard.append([types.InlineKeyboardButton("Remove", callback_data=f"sudo_rm:{viewer_id}:{page}:{target_id}")])
    keyboard.append([types.InlineKeyboardButton("Back", callback_data=f"sudo_page:{viewer_id}:{page}")])
    return text, types.InlineKeyboardMarkup(keyboard)


def _viewer_allowed(query: types.CallbackQuery, viewer_id: int) -> bool:
    return bool(query.from_user and query.from_user.id == viewer_id)


def _resolve_addsudo_target(message: types.Message) -> tuple[int | None, str | None]:
    if len(message.command) >= 2 and message.command[1].isdigit():
        return int(message.command[1]), message.command[2] if len(message.command) >= 3 else None

    replied_user = message.reply_to_message.from_user if message.reply_to_message else None
    if replied_user:
        return replied_user.id, message.command[1] if len(message.command) >= 2 else None

    return None, None


@app.on_message(filters.command(["addsudo", "setsudo", "setrole"]) & filters.user(config.OWNER_ID))
@handle_errors
async def addsudo_handler(_, message: types.Message):
    target_id, role_arg = _resolve_addsudo_target(message)
    if not target_id:
        return await message.reply_text(
            f"❌ Usage: <code>/addsudo &lt;user_id&gt; [moderator|uploader]</code>\n"
            f"Or reply with <code>/addsudo [moderator|uploader]</code>.\n"
            f"{_role_help()}",
            parse_mode=enums.ParseMode.HTML,
        )
    try:
        if target_id == config.OWNER_ID:
            return await message.reply_text("Owner role is configured with config.OWNER_ID.", parse_mode=enums.ParseMode.HTML)

        if not role_arg:
            keyboard = types.InlineKeyboardMarkup([
                [
                    types.InlineKeyboardButton("Moderator", callback_data=f"sudo_role:{message.from_user.id}:0:{target_id}:moderator"),
                    types.InlineKeyboardButton("Uploader", callback_data=f"sudo_role:{message.from_user.id}:0:{target_id}:uploader"),
                ],
                [types.InlineKeyboardButton("Sudo List", callback_data=f"sudo_page:{message.from_user.id}:0")],
            ])
            return await message.reply_text(
                f"Choose a sudo role for <code>{target_id}</code>.",
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML,
            )

        role = normalize_role(role_arg)
        if role not in MANAGED_ROLES:
            return await message.reply_text(f"❌ Invalid role. {_role_help()}", parse_mode=enums.ParseMode.HTML)

        meta = await _set_sudo_role(target_id, role)
        keyboard = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("Moderator", callback_data=f"sudo_role:{message.from_user.id}:0:{target_id}:moderator"),
                types.InlineKeyboardButton("Uploader", callback_data=f"sudo_role:{message.from_user.id}:0:{target_id}:uploader"),
            ],
            [
                types.InlineKeyboardButton("Remove", callback_data=f"sudo_rm:{message.from_user.id}:0:{target_id}"),
                types.InlineKeyboardButton("Sudo List", callback_data=f"sudo_page:{message.from_user.id}:0"),
            ],
        ])
        await message.reply_text(
            f"✅ User <code>{target_id}</code> set as <b>{meta['label']}</b> <code>{meta['symbol']} {meta['tag']}</code>.",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
        )
        LOGGER.info(f"Sudo role set: {target_id} -> {role} by {message.from_user.id}")
    except Exception as e:
        LOGGER.error(f"Error adding sudo: {e}")
        await message.reply_text("❌ <b>Database Error:</b> Failed to add user.", parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("rmsudo") & filters.user(config.OWNER_ID))
@handle_errors
async def rmsudo_handler(_, message: types.Message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Provide a User ID.", parse_mode=enums.ParseMode.HTML)
    try:
        target_id = int(message.command[1])
        res = await _remove_sudo_role(target_id)
        if res.deleted_count > 0:
            await message.reply_text(f"✅ User <code>{target_id}</code> removed from sudo list.", parse_mode=enums.ParseMode.HTML)
        else:
            await message.reply_text("❌ User not found in sudo list.", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Error removing sudo: {e}")
        await message.reply_text("❌ <b>Database Error:</b> Failed to remove user.", parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("sudolist") & sudo_filter)
@handle_errors
async def sudolist_handler(_, message: types.Message):
    text, markup = await _build_sudo_list_page(message.from_user.id, 0)
    await message.reply_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


@app.on_callback_query(filters.regex(r"^sudo_page:"))
async def sudo_page_callback(_, query: types.CallbackQuery):
    _, viewer_id, page = query.data.split(":")
    viewer_id = int(viewer_id)
    if not _viewer_allowed(query, viewer_id):
        return await query.answer("This menu is not for you.", show_alert=True)
    text, markup = await _build_sudo_list_page(viewer_id, int(page))
    await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    await query.answer()


@app.on_callback_query(filters.regex(r"^sudo_view:"))
async def sudo_view_callback(_, query: types.CallbackQuery):
    _, viewer_id, page, target_id = query.data.split(":")
    viewer_id = int(viewer_id)
    if not _viewer_allowed(query, viewer_id):
        return await query.answer("This menu is not for you.", show_alert=True)
    text, markup = await _build_sudo_detail(viewer_id, int(page), int(target_id))
    await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    await query.answer()


@app.on_callback_query(filters.regex(r"^sudo_role:"))
async def sudo_role_callback(_, query: types.CallbackQuery):
    _, viewer_id, page, target_id, role = query.data.split(":")
    viewer_id = int(viewer_id)
    target_id = int(target_id)
    page = int(page)
    if not _viewer_allowed(query, viewer_id):
        return await query.answer("This menu is not for you.", show_alert=True)
    if query.from_user.id != config.OWNER_ID:
        return await query.answer("Only the owner can change sudo roles.", show_alert=True)
    if target_id == config.OWNER_ID:
        return await query.answer("Owner role is configured with config.OWNER_ID.", show_alert=True)
    role = normalize_role(role)
    if role not in MANAGED_ROLES:
        return await query.answer("Invalid role.", show_alert=True)

    await _set_sudo_role(target_id, role)
    text, markup = await _build_sudo_detail(viewer_id, page, target_id)
    await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    await query.answer("Role updated.")


@app.on_callback_query(filters.regex(r"^sudo_rm:"))
async def sudo_remove_callback(_, query: types.CallbackQuery):
    _, viewer_id, page, target_id = query.data.split(":")
    viewer_id = int(viewer_id)
    target_id = int(target_id)
    page = int(page)
    if not _viewer_allowed(query, viewer_id):
        return await query.answer("This menu is not for you.", show_alert=True)
    if query.from_user.id != config.OWNER_ID:
        return await query.answer("Only the owner can remove sudo roles.", show_alert=True)
    if target_id == config.OWNER_ID:
        return await query.answer("Owner cannot be removed.", show_alert=True)

    res = await _remove_sudo_role(target_id)
    text, markup = await _build_sudo_list_page(viewer_id, page)
    await query.message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    await query.answer("Removed." if res.deleted_count else "User was not in sudo list.")


@app.on_callback_query(filters.regex(r"^sudo_close:"))
async def sudo_close_callback(_, query: types.CallbackQuery):
    _, viewer_id = query.data.split(":")
    viewer_id = int(viewer_id)
    if not _viewer_allowed(query, viewer_id):
        return await query.answer("This menu is not for you.", show_alert=True)
    await query.message.delete()
    await query.answer()
