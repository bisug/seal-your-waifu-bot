import asyncio

from Grabber import app, game_bot, userbot

IS_STARTED = False

async def start_bots():
    global IS_STARTED
    if IS_STARTED:
        return
    IS_STARTED = True

    try:
        from Grabber.database import sudo_collection
        from Grabber import sudo_users, LOGGER
        
        # Load Sudo Users from Database
        cursor = sudo_collection.find({})
        db_sudos = await cursor.to_list(length=None)
        
        loaded_count = 0
        for s in db_sudos:
            user_id = s.get('user_id')
            if user_id and user_id not in sudo_users:
                sudo_users.append(user_id)
                loaded_count += 1
                
        if loaded_count > 0:
            LOGGER.info(f"Loaded {loaded_count} sudo users from database.")
    except Exception as e:
        from Grabber import LOGGER
        LOGGER.error(f"Failed to load sudo users from DB: {e}")
    # Fix for ASGI (Uvicorn/Hypercorn) event loop mismatch
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

    try:
        await app.start()
        await game_bot.start()
    except AttributeError as e:
        if "API key is required" in str(e):
            from Grabber import LOGGER
            LOGGER.critical("CRITICAL: API_ID and API_HASH are missing or invalid in environment variables!")
            LOGGER.critical("Please set API_ID and API_HASH to start the bot.")
            IS_STARTED = False
            return
        raise e
    if userbot:
        from pyrogram.errors import AuthKeyInvalid, AuthKeyDuplicated, AuthKeyUnregistered, Unauthorized
        try:
            await userbot.start()
        except (AuthKeyInvalid, AuthKeyDuplicated, AuthKeyUnregistered, Unauthorized) as e:
            from Grabber import LOGGER
            LOGGER.warning(f"UserBot failed to start (Auth Issue): {e}")
            LOGGER.warning("Scraper features will be disabled until STRING_SESSION is updated.")
        except Exception as e:
            from Grabber import LOGGER
            if "AuthKeyNotFound" in type(e).__name__ or "Auth key not found" in str(e):
                LOGGER.warning(f"UserBot failed to start (Session Not Found): {e}")
                LOGGER.warning("Scraper features will be disabled until a valid STRING_SESSION is added.")
            else:
                LOGGER.error(f"UserBot failed to start (Unexpected): {e}")
    from Grabber.core.resources import start_resource_monitor
    start_resource_monitor()


async def stop_bots():
    global IS_STARTED
    from Grabber import LOGGER
    from Grabber.core.resources import stop_resource_monitor
    from Grabber.core.tasks import cancel_background_tasks
    from Grabber.database import close_connections

    await stop_resource_monitor()
    await cancel_background_tasks()

    for bot in (app, game_bot, userbot):
        if not bot:
            continue
        try:
            if getattr(bot, "is_connected", False):
                await bot.stop()
        except Exception as e:
            LOGGER.warning(f"Failed to stop {getattr(bot, 'name', type(bot).__name__)} cleanly: {e}")
    await close_connections()
    IS_STARTED = False
