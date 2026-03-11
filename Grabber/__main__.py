import importlib
import asyncio
import re

from pyrogram import filters, types, idle
from pyrogram.handlers import MessageHandler

from Grabber import (
    app, nguess_bot, LOGGER, start_bots, stop_bots
)
from Grabber.modules import ALL_MODULES
from Grabber.core.message_counter import message_counter


async def main():
    await start_bots()
    LOGGER.info("Bots started. Idling...")
    await idle()
    await stop_bots()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
