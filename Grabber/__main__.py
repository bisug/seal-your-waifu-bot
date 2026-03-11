import asyncio
import nest_asyncio

# Apply nest_asyncio FIRST — before any other imports.
# kurigram (Pyrogram fork) internally uses asyncio.get_event_loop() in its Session
# class, which on Python 3.13 can reference a different loop than the one running main().
# nest_asyncio patches asyncio to be re-entrant and loop-agnostic, fixing this.
nest_asyncio.apply()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import idle
from Grabber import app, nguess_bot, LOGGER, start_bots, stop_bots


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
