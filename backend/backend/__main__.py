import asyncio

from pyrogram import idle

from backend.core.logging import configure_event_loop_logging, get_logger
from backend.runner import start_bots, stop_bots

LOGGER = get_logger(__name__)


async def main():
    configure_event_loop_logging()
    await start_bots()
    LOGGER.info("Bots started. Idling...")
    await idle()
    await stop_bots()

if __name__ == "__main__":
    asyncio.run(main())
