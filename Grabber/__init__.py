import importlib
import re
import time
import logging
import asyncio
from pyrogram import Client, enums, types, filters
from pyrogram.handlers import MessageHandler
from config import config
from Grabber.database import (
    client, db, collection, group_collection,
    user_totals_collection, message_counts_collection,
    user_collection, group_user_totals_collection,
    top_global_groups_collection, total_pm_users, sudo_collection,
    spawns_collection, sessions_collection, quiz_questions_collection,
    nguess_enabled_groups_collection
)

StartTime = time.time()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)

OWNER_ID = config.OWNER_ID
sudo_users = config.SUDO_USERS
GROUP_ID = config.GROUP_ID
SUPPORT_ID = config.SUPPORT_ID
SUPPORT_GROUP_ID = config.SUPPORT_GROUP_ID
TOKEN =""
PHOTO_URL = config.PHOTO_URL
SUPPORT_CHAT = config.SUPPORT_CHAT
UPDATE_CHAT = config.UPDATE_CHAT
BOT_USERNAME = config.BOT_USERNAME
BOT_ID = None
BOT_NAME = None
CHARA_CHANNEL_ID = config.CHARA_CHANNEL_ID
WEB_APP_URL = config.WEB_APP_URL

class SealClient(Client):
    """
    Custom Client subclass for Seal-Bot.
    Consolidated into __init__.py for simpler project structure.
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

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)

        # 1. Fetch identity and update config (Only for MainBot)
        me = await self.get_me()
        if self.name == "MainBot":
            config.BOT_USERNAME = me.username
            config.BOT_ID = me.id
            config.BOT_NAME = me.first_name

            global BOT_USERNAME, BOT_ID, BOT_NAME
            BOT_USERNAME = me.username
            BOT_ID = me.id
            BOT_NAME = me.first_name

        # 2. Register Global Handlers
        if self.name == "MainBot":
            from Grabber.core.message_counter import message_counter
            self.add_handler(MessageHandler(message_counter, filters.group & ~filters.command(["seal", "messagecount"])), group=1)

        # 3. Load Modules
        from Grabber.modules import ALL_MODULES
        for module_name in ALL_MODULES:
            try:
                importlib.import_module(f"Grabber.modules.{module_name}")
            except Exception as e:
                LOGGER.error(f"Failed to load module {module_name}: {e}")
        LOGGER.info(f"Loaded {len(ALL_MODULES)} modules.")

        # 4. Set Bot Commands
        await self._set_commands_internal()

        if self.name == "MainBot":
            # 5. Ensure DB indexes are created (only needs to run once)
            from Grabber.database import seal_db
            await seal_db.ensure_indexes()

            # 6. Start Persistent Deletion Worker
            from Grabber.core.deletion import deletion_worker
            asyncio.create_task(deletion_worker())

            # 7. Start cache flush worker to persist in-memory state to DB
            from Grabber.core.spawns import flush_cache_to_db
            asyncio.create_task(flush_cache_to_db())

            # 8. Automate Mini App Menu Button
            try:
                await self.set_chat_menu_button(
                    menu_button=types.MenuButtonWebApp(
                        text="Shop",
                        web_app=types.WebAppInfo(url=f"{config.WEB_APP_URL}#shop")
                    )
                )
                LOGGER.info("Mini App Menu Button (Shop) configured successfully.")
            except Exception as e:
                LOGGER.error(f"Failed to configure Mini App Menu Button: {e}")

        LOGGER.info(f"SealClient started as {me.first_name} (@{me.username}).")

    async def _set_commands_internal(self):
        try:
            from Grabber.modules.info.start import HELP_DATA
            commands = []
            command_pattern = re.compile(r"🔹\s+.*?/(?P<cmd>\w+).*?\s+-\s+(?P<desc>.+)")
            seen_commands = set()

            # Define which commands belong to which bot client
            NGUESS_CMDS = ["nguess"]
            COMMON_CMDS = ["start", "help"]

            for key, category in HELP_DATA.items():
                # Skip Owner/Admin commands completely for the public command list
                if key == "OWNER":
                    continue

                if "text" in category:
                    for line in category["text"].split("\n"):
                        match = command_pattern.search(line)
                        if match:
                            cmd = match.group("cmd")
                            desc = match.group("desc").strip()

                            if self.name == "NguessBot":
                                # NguessBot only shows nguess + basic commands
                                if cmd not in NGUESS_CMDS and cmd not in COMMON_CMDS:
                                    continue
                            else:
                                # MainBot shows everything EXCEPT nguess and owner commands
                                if cmd in NGUESS_CMDS:
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

app = SealClient(name="MainBot", bot_token=config.TOKEN)
nguess_bot = SealClient(name="NguessBot", bot_token=config.SUB_TOKEN)

# For backward compatibility and modularity
Grabberu = app

async def start_bots():
    await app.start()
    await nguess_bot.start()

async def stop_bots():
    await app.stop()
    await nguess_bot.stop()
