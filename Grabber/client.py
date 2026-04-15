import asyncio
import importlib
import logging
import re

from pyrogram import Client, enums, errors, filters, types
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler

from config import config

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
        except errors.FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait limit reached for {chat_id}")
                return None
            await asyncio.sleep(e.value)
            return await self.send_message_safe(chat_id, text, *args, _retries=_retries+1, **kwargs)
        except (errors.PeerIdInvalid, errors.ChannelInvalid) as e:
            if _retries == 0:
                LOGGER.info(f"[{self.name}] Resolving peer {chat_id} after {type(e).__name__}")
                await self.resolve_peer_safe(chat_id)
                return await self.send_message_safe(chat_id, text, *args, _retries=1, **kwargs)
            LOGGER.error(f"[{self.name}] Peer resolution failed for {chat_id}: {e}")
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
        except errors.FloodWait as e:
            if _retries >= 2: return None
            await asyncio.sleep(e.value)
            return await self.send_media_safe(chat_id, media_url, *args, _retries=_retries+1, **kwargs)
        except (errors.PeerIdInvalid, errors.ChannelInvalid) as e:
            if _retries == 0:
                await self.resolve_peer_safe(chat_id)
                return await self.send_media_safe(chat_id, media_url, *args, _retries=1, **kwargs)
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
        except errors.FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            return await self.edit_message_text_safe(chat_id, message_id, text, *args, _retries=_retries+1, **kwargs)
        except Exception as e:
            # Silently ignore "Message is not modified" errors which are common
            if "MESSAGE_NOT_MODIFIED" not in str(e):
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
        except errors.FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            return await self.edit_message_caption_safe(chat_id, message_id, caption, *args, _retries=_retries+1, **kwargs)
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                LOGGER.error(f"[{self.name}] Error editing message caption in {chat_id}: {e}")
            return None

    async def edit_message_reply_markup_safe(self, chat_id, message_id, reply_markup, *args, _retries=0, **kwargs):
        """Edits message reply markup while handling FloodWait."""
        try:
            return await self.edit_message_reply_markup(chat_id, message_id, reply_markup, *args, **kwargs)
        except errors.FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            return await self.edit_message_reply_markup_safe(chat_id, message_id, reply_markup, *args, _retries=_retries+1, **kwargs)
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
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
            except Exception as e:
                LOGGER.error(f"Failed to load {module_name}: {e}")
                import traceback
                LOGGER.error(traceback.format_exc())
        LOGGER.info(f"Loaded {len(ALL_MODULES)} modules.")

        # Sync bot commands with Telegram
        if self.name != "UserBot":
            await self._set_commands_internal()

        if self.name == "MainBot":
            from Grabber.database import seal_db
            await seal_db.ensure_indexes()

            from Grabber.core.deletion import deletion_worker
            asyncio.create_task(deletion_worker())

            from Grabber.core.spawns import flush_cache_to_db
            asyncio.create_task(flush_cache_to_db())

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
                asyncio.create_task(send_startup_report(self, config.LOG_GROUP_ID, len(ALL_MODULES)))
            except Exception as e:
                LOGGER.warning(f"Failed to initiate startup report: {e}")

        LOGGER.info(f"SealClient started as {me.first_name} (@{me.username}).")

    async def _set_commands_internal(self):
        try:
            from Grabber.modules.info.start import HELP_DATA
            commands = []
            command_pattern = re.compile(r"🔹\s+.*?/(?P<cmd>\w+).*?\s+-\s+(?P<desc>.+)")
            seen_commands = set()

            # Define bot-specific command lists
            GAMEBOT_CMDS = {
                "nguess": "Start an anime character name guessing game",
                "quiz": "Test your anime knowledge & win Shards!",
                "scramble": "Unscramble the shuffled character name"
            }
            COMMON_CMDS = {
                "start": "Start the bot & interactive intro",
                "help": "Show available commands and usage guide",
                "profile": "View your stats & character collection",
                "balance": "Check Shards & Zenith balance"
            }

            if self.name == "GameBot":
                # GameBot: Only Games + Common
                # 1. Add common commands first
                for cmd, desc in COMMON_CMDS.items():
                    commands.append(types.BotCommand(command=cmd, description=desc))
                    seen_commands.add(cmd)
                
                # 2. Add game-specific commands
                for cmd, desc in GAMEBOT_CMDS.items():
                    if cmd not in seen_commands:
                        commands.append(types.BotCommand(command=cmd, description=desc))
                        seen_commands.add(cmd)
            else:
                # MainBot: All categories EXCEPT Games and Owner
                for key, category in HELP_DATA.items():
                    if key in ["OWNER", "GAMES"]:
                        continue

                    if "text" in category:
                        for line in category["text"].split("\n"):
                            match = command_pattern.search(line)
                            if match:
                                cmd = match.group("cmd")
                                desc = match.group("desc").strip()
                                
                                # Safety: ensure we don't accidentally leak owner commands if they were in HELP_DATA
                                if cmd in ["ngon", "ngoff", "nglist"]:
                                    continue
                                    
                                if cmd not in seen_commands:
                                    commands.append(types.BotCommand(command=cmd, description=desc[:100]))
                                    seen_commands.add(cmd)

            if "start" not in seen_commands:
                commands.append(types.BotCommand("start", "Start the bot"))

            if commands:
                await self.set_bot_commands(commands)
                LOGGER.info(f"Registered {len(commands)} commands for {self.name}.")
        except Exception as e:
            LOGGER.error(f"Failed to set commands for {self.name}: {e}")

    async def stop(self, *args):
        await super().stop()
        LOGGER.info(f"{self.name} stopped.")
