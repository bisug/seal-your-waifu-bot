from pyrogram import Client, enums
from config import config
import logging

LOGGER = logging.getLogger(__name__)

class SealClient(Client):
    """
    Custom Client subclass for Seal-Bot.
    
    This replaces the global monkey-patching approach with a proper Class-based structure.
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
            # We can use native plugin loading if we want, but keeping manual main loader for now to preserve order.
            # plugins=dict(root="Grabber/modules") 
        )

    async def start(self):
        await super().start()
        LOGGER.info("SealClient started.")

    async def stop(self, *args):
        await super().stop()
        LOGGER.info("SealClient stopped.")

# Initialize the client
app = SealClient()
