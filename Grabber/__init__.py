import importlib
import re
import time
import logging
from pyrogram import Client, enums, types, filters
from pyrogram.handlers import MessageHandler
from config import config
from Grabber.database import (
    client, db, collection, group_collection, 
    user_totals_collection, message_counts_collection, 
    user_collection, group_user_totals_collection, 
    top_global_groups_collection, total_pm_users, sudo_collection,
    spawns_collection, sessions_collection, quiz_questions_collection
)

                  
StartTime = time.time()

               
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)

                                         
OWNER_ID = config.OWNER_ID
sudo_users = config.SUDO_USERS
GROUP_ID = config.GROUP_ID
SUPPORT_ID = config.SUPPORT_ID
SUPPORT_GROUP_ID = config.SUPPORT_GROUP_ID
TOKEN = config.TOKEN
PHOTO_URL = config.PHOTO_URL
SUPPORT_CHAT = config.SUPPORT_CHAT
UPDATE_CHAT = config.UPDATE_CHAT
BOT_USERNAME = config.BOT_USERNAME
BOT_ID = None
BOT_NAME = None
CHARA_CHANNEL_ID = config.CHARA_CHANNEL_ID
JOINLOGS = config.JOINLOGS
LEAVELOGS = config.LEAVELOGS

class SealClient(Client):
    """
    Custom Client subclass for Seal-Bot.
    Consolidated into __init__.py for simpler project structure.
    """
    def __init__(self):
        super().__init__(
            name="Grabber",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.TOKEN,
            app_version="Seal-Bot v2",
            device_model="Seal-Server",
            system_version="Linux",
            workdir="Grabber",
        )

    async def start(self):
        await super().start()
        
        # 1. Fetch identity and update config
        me = await self.get_me()
        config.BOT_USERNAME = me.username
        config.BOT_ID = me.id
        config.BOT_NAME = me.first_name
        
        global BOT_USERNAME, BOT_ID, BOT_NAME
        BOT_USERNAME = me.username
        BOT_ID = me.id
        BOT_NAME = me.first_name

        # 2. Register Global Handlers
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
        
        LOGGER.info(f"SealClient started as {me.first_name} (@{me.username}).")

    async def _set_commands_internal(self):
        try:
            from Grabber.modules.start import HELP_DATA
            commands = []
            command_pattern = re.compile(r"🔹\s+[`]?/(?P<cmd>\w+)[^`]*[`]?\s+-\s+(?P<desc>.+)")
            seen_commands = set()
            
            for category in HELP_DATA.values():
                if "text" in category:
                    for line in category["text"].split("\n"):
                        match = command_pattern.search(line)
                        if match:
                            cmd = match.group("cmd")
                            desc = match.group("desc").strip()
                            if cmd not in seen_commands:
                                commands.append(types.BotCommand(command=cmd, description=desc[:100]))
                                seen_commands.add(cmd)
            
            if "start" not in seen_commands:
                commands.append(types.BotCommand("start", "Start the bot"))
                
            if commands:
                await self.set_bot_commands(commands)
                LOGGER.info(f"Registered {len(commands)} commands.")
        except Exception as e:
            LOGGER.error(f"Failed to set commands: {e}")

    async def stop(self, *args):
        await super().stop()
        LOGGER.info("SealClient stopped.")

                                                              
app = SealClient()
Grabberu = app
