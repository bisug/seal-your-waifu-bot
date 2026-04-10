"""
Telegram Bot session management (inline bot sessions for multi-step flows).
Backed by Redis with MongoDB fallback. Session IDs are short-lived keys
like 'trade:{id}' or 'battle:{chat_id}'.

Note: This is separate from the WebApp auth tokens in webapp/auth.py.
"""
from Grabber.core.cache import (
    create_session,
    get_session,
    delete_session
)

__all__ = ["create_session", "get_session", "delete_session"]
