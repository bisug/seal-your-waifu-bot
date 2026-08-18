import asyncio
import importlib
import re
import time

from pyrogram import Client, enums, errors, filters, raw, types
from pyrogram.handlers import MessageHandler

# Strip geo from inline queries. kurigram 2.2.24 still builds
# types.Location(..., client=client) in InlineQuery._parse, but Location.__init__
# rejects `client`, crashing every geo inline query before any handler runs.
# We never use query.location, so drop it at parse time.
_orig_inline_parse = types.InlineQuery._parse


@staticmethod
def _inline_query_parse_no_geo(client, inline_query, users):
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
        from_user=types.User._parse(client, users[inline_query.user_id]),
        query=inline_query.query,
        offset=inline_query.offset,
        chat_type=chat_type,
        location=None,
        client=client,
    )


types.InlineQuery._parse = _inline_query_parse_no_geo

from config import config
from Grabber.core.logging import get_logger, install_exception_hooks, setup_logging

setup_logging()
install_exception_hooks()

from Grabber.client import SealClient
from Grabber.database import (client, collection, db,
                              global_group_bans_collection,
                              global_user_bans_collection,
                              group_collection, group_user_totals_collection,
                              message_counts_collection, pet_catalog_collection,
                              quiz_questions_collection,
                              scraped_characters_collection, sessions_collection,
                              spawns_collection, sudo_collection,
                              total_pm_users, user_collection,
                              user_totals_collection)

StartTime = time.time()

LOGGER = get_logger(__name__)

OWNER_ID = config.OWNER_ID
sudo_users = config.SUDO_USERS
sudo_roles = {int(user_id): "moderator" for user_id in sudo_users}
MAIN_GROUP_ID = config.MAIN_GROUP_ID
TOKEN = config.TOKEN
PHOTO_URL = config.PHOTO_URL
SUPPORT_CHAT = config.SUPPORT_CHAT
UPDATE_CHAT = config.UPDATE_CHAT
BOT_USERNAME = config.BOT_USERNAME
GAME_BOT_USERNAME = None
BOT_ID = None
BOT_NAME = None
GALLERY_CHANNEL_ID = config.GALLERY_CHANNEL_ID
WEB_APP_URL = config.WEB_APP_URL
WEB_APP_URL = config.WEB_APP_URL


app = SealClient(name="MainBot", bot_token=config.TOKEN)
game_bot = SealClient(name="GameBot", bot_token=config.SUB_TOKEN)
userbot = SealClient(name="UserBot", session_string=config.STRING_SESSION) if config.STRING_SESSION else None

# For backward compatibility and modularity
Grabber = app
nguess_bot = game_bot

def _sudo_check(flt, client, message):
    if not message.from_user:
        return False
    from Grabber.core.roles import moderator

    return moderator(message.from_user.id)

sudo_filter = filters.create(_sudo_check)


def _uploader_check(flt, client, message):
    if not message.from_user:
        return False
    from Grabber.core.roles import can_upload

    return can_upload(message.from_user.id)


uploader_filter = filters.create(_uploader_check)
