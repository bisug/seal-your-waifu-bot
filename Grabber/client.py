import asyncio
import importlib
import logging
import re

from pyrogram import Client, enums, errors, filters, types
from pyrogram.errors import FloodWait
from pyrogram.handlers import MessageHandler

from config import config
from Grabber.core.tasks import run_background_task

LOGGER = logging.getLogger(__name__)

class SealClient(Client):
    """Custom Telegram Client for the Seal bot ecosystem."""
    def __init__(self, name="Grabber", bot_token=None, session_string=None):
        # Determine if we're using a bot token or a session string
        actual_bot_token = bot_token if not session_string else None
        if not actual_bot_token and not session_string and name != "UserBot":
            actual_bot_token = config.TOKEN

        super().__init__(
            name=name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=actual_bot_token,
            session_string=session_string,
            app_version="Seal-Bot v2",
            device_model="Seal-Server",
            system_version="Linux",
            workdir="Grabber")
        self._kurigram_error_handler_registered = False
        self._register_kurigram_error_handler()

    def _register_kurigram_error_handler(self):
        """Register Kurigram's global handler-error hook when available."""
        if self._kurigram_error_handler_registered or not hasattr(self, "on_error"):
            return

        @self.on_error(group=-1)
        async def _log_kurigram_handler_error(client, exception, handler, *raw_args):
            callback = getattr(handler, "callback", None)
            handler_name = getattr(callback, "__qualname__", type(handler).__name__)
            update_type = type(raw_args[0]).__name__ if raw_args else "unknown"
            exc_info = (type(exception), exception, exception.__traceback__)

            LOGGER.error(
                "[%s] Unhandled Kurigram handler error in %s for %s",
                getattr(client, "name", self.name),
                handler_name,
                update_type,
                exc_info=exc_info,
            )

        self._kurigram_error_handler_registered = True

    async def resolve_peer_safe(self, chat_id):
        """Attempts to resolve a peer ID in the bot's cache to avoid PeerIdInvalid errors."""
        try:
            if isinstance(chat_id, int):
                # Only attempt background resolution for numeric IDs
                await self.get_chat(chat_id)
                return True
        except Exception:
            pass
        return False

    async def send_message_safe(self, chat_id, text, *args, _retries=0, **kwargs):
        """Sends a message while handling FloodWait, Peer resolution, and auto-deletion."""
        auto_delete = kwargs.pop("auto_delete", 0)
        
        # Handle reply_parameters logic
        if "reply_to_message_id" in kwargs and "reply_parameters" not in kwargs:
            reply_id = kwargs.pop("reply_to_message_id")
            if reply_id:
                kwargs["reply_parameters"] = types.ReplyParameters(message_id=reply_id)

        try:
            msg = await self.send_message(chat_id, text, *args, **kwargs)
            if msg and auto_delete:
                from Grabber.core.deletion import schedule_deletion
                await schedule_deletion(chat_id, msg.id, auto_delete, bot_name=self.name)
            return msg
        except FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait limit reached for {chat_id}")
                return None
            await asyncio.sleep(e.value)
            return await self.send_message_safe(chat_id, text, *args, _retries=_retries+1, **kwargs)
        except errors.SlowmodeWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] SlowmodeWait limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] SlowmodeWait for {chat_id}: {e.value}s")
            await asyncio.sleep(e.value)
            return await self.send_message_safe(chat_id, text, *args, _retries=_retries+1, **kwargs)
        except (errors.PeerIdInvalid, errors.ChannelInvalid) as e:
            if _retries == 0:
                LOGGER.info(f"[{self.name}] Resolving peer {chat_id} after {type(e).__name__}")
                await self.resolve_peer_safe(chat_id)
                return await self.send_message_safe(chat_id, text, *args, _retries=1, **kwargs)
            LOGGER.error(f"[{self.name}] Peer resolution failed for {chat_id}: {e}")
            return None
        except (errors.Forbidden, errors.Unauthorized) as e:
            LOGGER.debug(f"[{self.name}] Permission denied in {chat_id}: {e}")
            return None
        except errors.BadRequest as e:
            LOGGER.error(f"[{self.name}] BadRequest in {chat_id}: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"[{self.name}] Failed to send message to {chat_id}: {e}")
            return None

    async def send_media_safe(self, chat_id, media_url, *args, _retries=0, **kwargs):
        """Sends a photo or video while handling FloodWait, Peer resolution, and auto-deletion."""
        auto_delete = kwargs.pop("auto_delete", 0)
        
        # Handle reply_parameters logic
        if "reply_to_message_id" in kwargs and "reply_parameters" not in kwargs:
            reply_id = kwargs.pop("reply_to_message_id")
            if reply_id:
                kwargs["reply_parameters"] = types.ReplyParameters(message_id=reply_id)

        try:
            from Grabber.core.utils import send_media_dynamic
            msg = await send_media_dynamic(self, chat_id, media_url, *args, **kwargs)
            if msg and auto_delete:
                from Grabber.core.deletion import schedule_deletion
                await schedule_deletion(chat_id, msg.id, auto_delete, bot_name=self.name)
            return msg
        except FloodWait as e:
            if _retries >= 2: return None
            await asyncio.sleep(e.value)
            return await self.send_media_safe(chat_id, media_url, *args, _retries=_retries+1, **kwargs)
        except errors.SlowmodeWait as e:
            if _retries >= 2: return None
            LOGGER.warning(f"[{self.name}] SlowmodeWait for {chat_id}: {e.value}s")
            await asyncio.sleep(e.value)
            return await self.send_media_safe(chat_id, media_url, *args, _retries=_retries+1, **kwargs)
        except (errors.PeerIdInvalid, errors.ChannelInvalid) as e:
            if _retries == 0:
                await self.resolve_peer_safe(chat_id)
                return await self.send_media_safe(chat_id, media_url, *args, _retries=1, **kwargs)
            return None
        except (errors.Forbidden, errors.Unauthorized) as e:
            LOGGER.debug(f"[{self.name}] Permission denied in {chat_id}: {e}")
            return None
        except errors.BadRequest as e:
            LOGGER.error(f"[{self.name}] BadRequest in {chat_id}: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"[{self.name}] Failed to send media to {chat_id}: {e}")
            return None

    async def edit_message_text_safe(self, chat_id, message_id, text, *args, _retries=0, **kwargs):
        """Edits message text while handling FloodWait."""
        # Handle reply_to_message_id deprecation (though less common for edits, for consistency)
        if "reply_to_message_id" in kwargs and "reply_parameters" not in kwargs:
            reply_id = kwargs.pop("reply_to_message_id")
            if reply_id:
                kwargs["reply_parameters"] = types.ReplyParameters(message_id=reply_id)

        try:
            return await self.edit_message_text(chat_id, message_id, text, *args, **kwargs)
        except FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            return await self.edit_message_text_safe(chat_id, message_id, text, *args, _retries=_retries+1, **kwargs)
        except errors.MessageNotModified:
            return None
        except (errors.Forbidden, errors.Unauthorized) as e:
            LOGGER.debug(f"[{self.name}] Permission denied in {chat_id}: {e}")
            return None
        except errors.BadRequest as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                LOGGER.error(f"[{self.name}] BadRequest in {chat_id}: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"[{self.name}] Error editing message text in {chat_id}: {e}")
            return None

    async def edit_message_caption_safe(self, chat_id, message_id, caption, *args, _retries=0, **kwargs):
        """Edits message caption while handling FloodWait."""
        # Handle reply_to_message_id deprecation
        if "reply_to_message_id" in kwargs and "reply_parameters" not in kwargs:
            reply_id = kwargs.pop("reply_to_message_id")
            if reply_id:
                kwargs["reply_parameters"] = types.ReplyParameters(message_id=reply_id)

        try:
            return await self.edit_message_caption(chat_id, message_id, caption, *args, **kwargs)
        except FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            return await self.edit_message_caption_safe(chat_id, message_id, caption, *args, _retries=_retries+1, **kwargs)
        except errors.MessageNotModified:
            return None
        except (errors.Forbidden, errors.Unauthorized) as e:
            LOGGER.debug(f"[{self.name}] Permission denied in {chat_id}: {e}")
            return None
        except errors.BadRequest as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                LOGGER.error(f"[{self.name}] BadRequest in {chat_id}: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"[{self.name}] Error editing message caption in {chat_id}: {e}")
            return None

    async def edit_message_reply_markup_safe(self, chat_id, message_id, reply_markup, *args, _retries=0, **kwargs):
        """Edits message reply markup while handling FloodWait."""
        try:
            return await self.edit_message_reply_markup(chat_id, message_id, reply_markup, *args, **kwargs)
        except FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            return await self.edit_message_reply_markup_safe(chat_id, message_id, reply_markup, *args, _retries=_retries+1, **kwargs)
        except errors.MessageNotModified:
            return None
        except (errors.Forbidden, errors.Unauthorized) as e:
            LOGGER.debug(f"[{self.name}] Permission denied in {chat_id}: {e}")
            return None
        except errors.BadRequest as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                LOGGER.error(f"[{self.name}] Error editing message markup in {chat_id}: {e}")
            return None
        except Exception as e:
            LOGGER.error(f"[{self.name}] Error editing message markup in {chat_id}: {e}")
            return None

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)

        import Grabber

        # Configure bot identity and store in config
        me = await self.get_me()
        self.username = me.username
        self.bot_id = me.id
        self.first_name = me.first_name

        if self.name == "MainBot":
            config.BOT_USERNAME = me.username
            config.BOT_ID = me.id
            config.BOT_NAME = me.first_name

            Grabber.BOT_USERNAME = me.username
            Grabber.BOT_ID = me.id
            Grabber.BOT_NAME = me.first_name
        else:
            Grabber.GAME_BOT_USERNAME = me.username

        # Dynamic Module Loading
        from Grabber.modules import ALL_MODULES
        for module_name in ALL_MODULES:
            try:
                module = importlib.import_module(f"Grabber.modules.{module_name}")
                if hasattr(module, "load_handlers"):
                    module.load_handlers(self)
                    LOGGER.info(f"Loaded (Explicit): {module_name}")
                else:
                    LOGGER.info(f"Loaded (Decorator): {module_name}")
            except Exception:
                LOGGER.exception("Failed to load %s", module_name)
        LOGGER.info(f"Loaded {len(ALL_MODULES)} modules.")

        # Sync bot commands with Telegram
        if self.name != "UserBot":
            await self._set_commands_internal()

        if self.name == "MainBot":
            from Grabber.database import r as redis_client
            from Grabber.database import seal_db
            await seal_db.ping()
            LOGGER.info("MongoDB connectivity verified.")
            if redis_client:
                try:
                    await redis_client.ping()
                    LOGGER.info("Redis connectivity verified.")
                except Exception as e:
                    LOGGER.warning(f"Redis ping failed; Redis-backed features will use fallbacks where available: {e}")
            await seal_db.ensure_indexes()
            from Grabber.core.pets import seed_pet_catalog
            await seed_pet_catalog()

            from Grabber.core.deletion import deletion_worker
            run_background_task(deletion_worker(), name="deletion-worker")

            from Grabber.core.spawns import flush_cache_to_db
            run_background_task(flush_cache_to_db(), name="spawn-cache-flush")

            # Configure Mini-App menu button
            try:
                await self.set_chat_menu_button(
                    menu_button=types.MenuButtonWebApp(
                        text="Shop",
                        web_app=types.WebAppInfo(url=f"{config.WEB_APP_URL}#shop")
                    )
                )
                LOGGER.info("Mini App Menu button configured.")
            except Exception as e:
                LOGGER.error(f"Failed to configure Mini App Menu button: {e}")

            # Send creative startup report to group
            try:
                from Grabber.core.startup import send_startup_report
                run_background_task(
                    send_startup_report(self, config.LOG_GROUP_ID, len(ALL_MODULES)),
                    name="startup-report",
                )
            except Exception as e:
                LOGGER.warning(f"Failed to initiate startup report: {e}")

        LOGGER.info(f"SealClient started as {me.first_name} (@{me.username}).")

    async def _set_commands_internal(self):
        try:
            commands = []
            
            # Simplified descriptions for GameBot
            GAMEBOT_CMDS = {
                "nguess": "Guess character name",
                "quiz": "Anime trivia quiz",
                "scramble": "Unscramble name",
                "top": "Global game stats",
                "stats": "GameBot totals",
                "help": "How to play"
            }
            
            # Simplified descriptions for MainBot (User-facing & Utilities)
            MAINBOT_CMDS = {
                # Core & Info
                "start": "Start the bot",
                "help": "Show help menu",
                "profile": "Collector profile",
                "balance": "Check Shards",
                "harem": "Your collection",
                "shop": "Open the shop",
                "top": "Global leaderboard",
                "daily": "Daily reward",
                "weekly": "Weekly reward",
                "bet": "Gamble Shards",
                "pay": "Pay a user",
                "sell": "Sell characters",
                "exchange": "Convert Shards",
                "zenith": "Shards to Zenith",
                "shard": "Zenith to Shards",
                "trade": "Trade characters",
                "gift": "Gift a character",
                "transfer": "Transfer full harem",
                "propose": "Propose to a user",
                "referrals": "Invite friends",
                "battle": "Start a PvP duel",
                "pass": "Battle Pass progress",
                "paysupport": "Payment support",
                "terms": "Purchase terms",
                "quests": "Active quests",
                "level": "Check your level",
                "achievements": "View milestones",
                "mypet": "Manage your pet",
                "petshop": "Buy pet items",
                "hunt": "Send pet to hunt",
                "eggs": "View your eggs",
                "hatch": "Hatch char eggs",
                "feed": "Feed your pet",
                "train": "Train your pet",
                "search": "Find a character",
                "fav": "Set favorite",
                "rarities": "Character counts",
                "animes": "List available anime",
                "sani": "Search by anime",
                "reedem": "Redeem waifugen code",
                "ping": "Check bot status",
                "stats": "Bot statistics",
                "ctop": "Chat leaderboard",
                "mtop": "Rich leaderboard",
                "webapp": "Open Mini-App",
                "check": "Check user status",
                "messagecount": "Your chat activity",
                "seal": "Use a seal item",
                "hmode": "Change harem display mode"
            }

            target_cmds = GAMEBOT_CMDS if self.name == "GameBot" else MAINBOT_CMDS
            
            for cmd, desc in target_cmds.items():
                commands.append(types.BotCommand(command=cmd, description=desc))

            if commands:
                await self.set_bot_commands(commands)
                LOGGER.info(f"Registered {len(commands)} commands for {self.name}.")
        except Exception as e:
            LOGGER.error(f"Failed to set commands for {self.name}: {e}")

    async def stop(self, *args):
        await super().stop()
        LOGGER.info(f"{self.name} stopped.")
