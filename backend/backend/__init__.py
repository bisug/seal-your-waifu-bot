"""Seal Bot package root.

Only bootstrap-level wiring lives here: the kurigram geo patch, logging
setup, and the sudo/uploader custom filters. Everything else has a real
home — import it from there:

- clients (app, game_bot)         -> backend.client
- DB collections                    -> backend.database
- sudo state (sudo_users/roles)     -> backend.core.roles
- chat IDs, URLs, identity          -> config
- loggers                          -> backend.core.logging (get_logger)
"""
import time

from pyrogram import enums, filters, raw, types

# Strip geo from inline queries. kurigram 2.2.24 still builds
# types.Location(..., client=client) in InlineQuery._parse, but Location.__init__
# rejects `client`, crashing every geo inline query before any handler runs.
# We never use query.location, so drop it at parse time.
_orig_inline_parse = types.InlineQuery._parse


@staticmethod
def _inline_query_parse_no_geo(bot_client, inline_query, users):
    peer_type = inline_query.peer_type
    chat_type = None
    if isinstance(peer_type, raw.types.InlineQueryPeerTypeSameBotPM):
        chat_type = enums.ChatType.BOT
    elif isinstance(peer_type, raw.types.InlineQueryPeerTypePM):
        chat_type = enums.ChatType.PRIVATE
    elif isinstance(peer_type, raw.types.InlineQueryPeerTypeChat):
        chat_type = enums.ChatType.GROUP
    elif isinstance(peer_type, raw.types.InlineQueryPeerTypeMegagroup):
        chat_type = enums.ChatType.SUPERGROUP
    elif isinstance(peer_type, raw.types.InlineQueryPeerTypeBroadcast):
        chat_type = enums.ChatType.CHANNEL
    return types.InlineQuery(
        id=str(inline_query.query_id),
        from_user=types.User._parse(bot_client, users[inline_query.user_id]),
        query=inline_query.query,
        offset=inline_query.offset,
        chat_type=chat_type,
        location=None,
        client=bot_client,
    )


types.InlineQuery._parse = _inline_query_parse_no_geo

from backend.core.logging import install_exception_hooks, setup_logging

setup_logging()
install_exception_hooks()

# Process start time, used by /ping uptime.
StartTime = time.time()


def _sudo_check(_, __, message):
    if not message.from_user:
        return False
    from backend.core.roles import moderator

    return moderator(message.from_user.id)

sudo_filter = filters.create(_sudo_check)


def _uploader_check(_, __, message):
    if not message.from_user:
        return False
    from backend.core.roles import can_upload

    return can_upload(message.from_user.id)


uploader_filter = filters.create(_uploader_check)
