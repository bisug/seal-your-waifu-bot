import importlib
import asyncio
import re

from pyrogram import filters, types, idle
from pyrogram.handlers import MessageHandler

from Grabber import (
    app, LOGGER
)
from Grabber.modules import ALL_MODULES
from Grabber.core.message_counter import message_counter

                                                                              

                                                                              
def load_plugins():
    for module_name in ALL_MODULES:
        importlib.import_module(f"Grabber.modules.{module_name}")
    LOGGER.info(f"Loaded {len(ALL_MODULES)} modules.")

async def set_bot_commands(client):
                                                                               
    from Grabber.modules.start import HELP_DATA
    
    commands = []
                                                                               
    command_pattern = re.compile(r"🔹\s+/(?P<cmd>\w+)(?:\s+<[^>]+>)*\s+-\s+(?P<desc>.+)")
    
    seen_commands = set()
    
    for category in HELP_DATA.values():
        if "text" in category:
            for line in category["text"].split("\n"):
                match = command_pattern.search(line)
                if match:
                    cmd = match.group("cmd")
                    desc = match.group("desc").strip()
                    
                    if cmd not in seen_commands:
                                                                     
                        commands.append(
                            types.BotCommand(
                                command=cmd,
                                description=desc[:100]
                            )
                        )
                        seen_commands.add(cmd)
    
                                               
    if "start" not in seen_commands:
        commands.append(types.BotCommand("start", "Start the bot and get welcome message"))
        
    if commands:
        try:
            await client.set_bot_commands(commands)
            LOGGER.info(f"Successfully registered {len(commands)} commands with Telegram.")
        except Exception as e:
            LOGGER.error(f"Failed to set bot commands: {e}")

async def main():
    """Main entry point using Pyrogram's startup sequence."""
    LOGGER.info("Initializing Seal-Bot...")
    
    app.add_handler(MessageHandler(message_counter, filters.group & ~filters.command(["seal", "messagecount"])), group=1)
    
    # 1. Start App first to connect
    await app.start()
    
    # 2. Fetch Bot Identity
    me = await app.get_me()
    LOGGER.info(f"Started as {me.first_name} (@{me.username})")
    
    # 3. Update Config & Global Variables
    from Grabber import config
    import Grabber
    
    config.BOT_USERNAME = me.username
    config.BOT_ID = me.id
    config.BOT_NAME = me.first_name
    
    Grabber.BOT_USERNAME = me.username
    Grabber.BOT_ID = me.id
    Grabber.BOT_NAME = me.first_name
    
    # 4. Load Plugins (Now they will see correct BOT_USERNAME)
    load_plugins()

    await set_bot_commands(app)
    LOGGER.info("Bot is now online and active!")
    
                          
    await idle()
    
                   
    await app.stop()
    LOGGER.info("Bot shut down cleanly.")

if __name__ == "__main__":
                                                                                      
    app.run(main())
