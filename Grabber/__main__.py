import asyncio
import nest_asyncio

# Patch asyncio to be re-entrant first
nest_asyncio.apply()

# Create our canonical event loop and set it as the global default
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import idle
from Grabber import app, game_bot, LOGGER, start_bots, stop_bots

# CRITICAL: kurigram's Session.send() calls self.client.loop.run_in_executor()
# which creates Futures anchored to self.client.loop. If that loop != the running
# loop, it crashes with "Future attached to a different loop".
# Force-patching here guarantees both clients use the exact loop that main() runs on.
app.loop = loop
game_bot.loop = loop


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
