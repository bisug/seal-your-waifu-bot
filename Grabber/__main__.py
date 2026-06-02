import asyncio

from pyrogram import enums, idle

import Grabber.core.sync_handler  # Register global message sync handlers
from Grabber import LOGGER, app, game_bot
from Grabber.core.logging import configure_event_loop_logging
from Grabber.runner import start_bots, stop_bots


async def main():
    configure_event_loop_logging()
    await start_bots()
    LOGGER.info("Bots started. Idling...")
    await idle()
    await stop_bots()

if __name__ == "__main__":
    asyncio.run(main())
