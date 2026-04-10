from Grabber import app, game_bot

async def start_bots():
    await app.start()
    await game_bot.start()

async def stop_bots():
    await app.stop()
    await game_bot.stop()
