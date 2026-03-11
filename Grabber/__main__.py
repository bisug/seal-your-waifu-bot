import asyncio

# CRITICAL: Create and set the event loop BEFORE importing Grabber.
# Pyrogram stores self.loop = asyncio.get_event_loop() when Client.__init__ runs.
# If the loop is created after import, clients bind to a different loop than main() runs on.
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
