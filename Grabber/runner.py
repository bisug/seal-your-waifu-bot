import asyncio

from Grabber import app, game_bot


async def start_bots():
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

    await app.start()
    await game_bot.start()

async def stop_bots():
    await app.stop()
    await game_bot.stop()
