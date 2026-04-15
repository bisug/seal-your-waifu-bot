import asyncio

from Grabber import app, game_bot, userbot

IS_STARTED = False

async def start_bots():
    global IS_STARTED
    if IS_STARTED:
        return
    IS_STARTED = True
    # Fix for ASGI (Hypercorn/Uvicorn) event loop mismatch
    loop = asyncio.get_running_loop()
    
    # Rebind MainBot
    app.loop = loop
    if hasattr(app, 'dispatcher'):
        app.dispatcher.loop = loop
        
    # Rebind GameBot
    game_bot.loop = loop
    if hasattr(game_bot, 'dispatcher'):
        game_bot.dispatcher.loop = loop

    # Rebind UserBot
    if userbot:
        userbot.loop = loop
        if hasattr(userbot, 'dispatcher'):
            userbot.dispatcher.loop = loop

    await app.start()
    await game_bot.start()
    if userbot:
        await userbot.start()

async def stop_bots():
    await app.stop()
    await game_bot.stop()
    if userbot:
        await userbot.stop()
