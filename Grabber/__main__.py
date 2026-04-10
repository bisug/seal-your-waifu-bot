import asyncio
import nest_asyncio

# Patch asyncio to be re-entrant first
nest_asyncio.apply()

# Create our canonical event loop and set it as the global default
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import idle
from Grabber import app, game_bot, LOGGER
from Grabber.runner import start_bots, stop_bots
import Grabber.core.sync_handler  # Register global message sync handlers




async def main():
    await start_bots()
    LOGGER.info("Bots started. Idling...")
    await idle()
    await stop_bots()

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
