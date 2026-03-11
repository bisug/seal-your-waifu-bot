"""
Session management — backed by Redis, with MongoDB fallback.
All session functions are re-exported from cache.py for backward compatibility.
"""
from Grabber.core.cache import (
    create_session,
    get_session,
    delete_session
)

__all__ = ["create_session", "get_session", "delete_session"]
