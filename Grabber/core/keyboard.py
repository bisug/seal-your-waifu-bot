from pyrogram import types, enums
from Grabber import WEB_APP_URL, BOT_USERNAME
from config import config

class KeyboardBuilder:
    def __init__(self):
        self.keyboard = []

    def add_button(self, text: str, callback_data: str = None, url: str = None, web_app: types.WebAppInfo = None, switch_inline_query_current_chat: str = None, style: enums.ButtonStyle = None):
        """Adds a single button to a new row."""
        self.keyboard.append([types.InlineKeyboardButton(
            text=text,
            callback_data=callback_data,
            url=url,
            web_app=web_app,
            switch_inline_query_current_chat=switch_inline_query_current_chat,
            style=style
        )])
        return self

    def add_row(self, *buttons: types.InlineKeyboardButton):
        """Adds multiple buttons to a single row."""
        self.keyboard.append(list(buttons))
        return self

    def build(self) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(self.keyboard)

def get_webapp_button(is_private: bool = True) -> types.InlineKeyboardButton:
    """Returns a standardized direct WebApp button only for groups (DM removed as per request)."""
    if is_private:
        return None
    return types.InlineKeyboardButton("Open Mini App", web_app=types.WebAppInfo(url=WEB_APP_URL), style=enums.ButtonStyle.PRIMARY)

def get_paginated_keyboard(page: int, total_pages: int, callback_prefix: str, user_id: int, is_private: bool = True) -> types.InlineKeyboardMarkup:
    """Builds a standard paginated keyboard with navigation and optional group WebApp link."""
    builder = KeyboardBuilder()
    
    # Navigation Row
    nav_row = []
    if total_pages > 1:
        if page > 0:
            nav_row.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"{callback_prefix}:p:{page-1}:{user_id}")) # Keeping arrows as they are functional
        if page < total_pages - 1:
            nav_row.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"{callback_prefix}:n:{page+1}:{user_id}")) # Keeping arrows as they are functional
    
    if nav_row:
        builder.add_row(*nav_row)
    
    # WebApp Button (Only added if not None)
    webapp_btn = get_webapp_button(is_private)
    if webapp_btn:
        builder.add_row(webapp_btn)
    
    return builder.build()
