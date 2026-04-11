import logging
import asyncio
import importlib
import re
from pyrogram import Client, types, errors, filters
from pyrogram.handlers import MessageHandler
from config import config

LOGGER = logging.getLogger(__name__)

class SealClient(Client):
    """
    Main entry point for the Seal Telegram Client.
    Handles initialization, module loading, and command registration.
    """
    def __init__(self, name="Grabber", bot_token=None):
        super().__init__(
            name=name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=bot_token or config.TOKEN,
            app_version="Seal-Bot v2",
            device_model="Seal-Server",
            system_version="Linux",
            workdir="Grabber")

    async def send_message_safe(self, chat_id, text, *args, _retries=0, **kwargs):
        """Sends a message while handling FloodWait and optional auto-deletion."""
        auto_delete = kwargs.pop("auto_delete", 0)
        
        # Handle reply_to_message_id deprecation
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
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            if auto_delete: kwargs["auto_delete"] = auto_delete
            return await self.send_message_safe(chat_id, text, *args, _retries=_retries+1, **kwargs)
        except Exception as e:
            LOGGER.error(f"[{self.name}] Error sending message to {chat_id}: {e}")
            return None

    async def send_media_safe(self, chat_id, media_url, *args, _retries=0, **kwargs):
        """Sends a photo or video while handling FloodWait and optional auto-deletion."""
        auto_delete = kwargs.pop("auto_delete", 0)
        
        # Handle reply_to_message_id deprecation
        if "reply_to_message_id" in kwargs and "reply_parameters" not in kwargs:
            reply_id = kwargs.pop("reply_to_message_id")
            if reply_id:
                kwargs["reply_parameters"] = types.ReplyParameters(message_id=reply_id)

        try:
            if isinstance(media_url, str) and media_url.endswith(('.mp4', '.webm', '.gif')):
                msg = await self.send_video(chat_id, video=media_url, *args, **kwargs)
            else:
                msg = await self.send_photo(chat_id, photo=media_url, *args, **kwargs)
            if msg and auto_delete:
                from Grabber.core.deletion import schedule_deletion
                await schedule_deletion(chat_id, msg.id, auto_delete, bot_name=self.name)
            return msg
        except errors.FloodWait as e:
            if _retries >= 3:
                LOGGER.error(f"[{self.name}] FloodWait retry limit reached for {chat_id}")
                return None
            LOGGER.warning(f"[{self.name}] FloodWait detected: Sleeping for {e.value}s")
            await asyncio.sleep(e.value)
            if auto_delete: kwargs["auto_delete"] = auto_delete
            return await self.send_media_safe(chat_id, media_url, *args, _retries=_retries+1, **kwargs)
        except Exception as e:
            LOGGER.error(f"[{self.name}] Error sending media to {chat_id}: {e}")
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

        # Register message counter for groups
        if self.name == "MainBot":
            from Grabber.core.message_counter import message_counter
            self.add_handler(MessageHandler(message_counter, filters.group & ~filters.command(["seal", "messagecount"])), group=1)

        # Load dynamic modules from modules package
        from Grabber.modules import ALL_MODULES
        for module_name in ALL_MODULES:
            try:
                importlib.import_module(f"Grabber.modules.{module_name}")
            except Exception as e:
                LOGGER.error(f"Failed to load module {module_name}: {e}")
        LOGGER.info(f"Loaded {len(ALL_MODULES)} modules.")

        # Sync bot commands with Telegram
        await self._set_commands_internal()

        if self.name == "MainBot":
            # Database and Background tasks
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
