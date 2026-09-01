import asyncio
import os
import uuid

from backend.client import app, game_bot, userbot
from backend.core.logging import get_logger
from backend.core.roles import sudo_roles, sudo_users

LOGGER = get_logger(__name__)

IS_STARTED = False
STARTUP_STATE = "stopped"
_START_LOCK = None

# Single-instance guard: MTProto sessions corrupt if two processes drive
# the same token concurrently. Redis-held lock; a second replica refuses to start.
_INSTANCE_LOCK_KEY = "sealbot:single_instance_lock"
_INSTANCE_LOCK_TTL = 60  # seconds; refreshed while running
# Unique per process, not per pid: containers both run uvicorn as pid 7.
_INSTANCE_ID = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
# Rolling deploys: old container holds the lock up to 60s drain + 60s TTL.
_INSTANCE_LOCK_WAIT_TIMEOUT = 180  # seconds
_INSTANCE_LOCK_RETRY_INTERVAL = 5  # seconds


async def _acquire_instance_lock(status: dict) -> bool:
    """Try to own the single-instance lock. Returns True if we may start."""
    from backend.core.tasks import run_background_task
    from backend.database import r as redis_client
    if not redis_client:
        LOGGER.warning(
            "Redis unavailable: multi-instance session lock disabled. "
            "Run exactly ONE process per deployment."
        )
        return True
    deadline = asyncio.get_running_loop().time() + _INSTANCE_LOCK_WAIT_TIMEOUT
    while True:
        try:
            owned = await redis_client.set(
                _INSTANCE_LOCK_KEY, _INSTANCE_ID, ex=_INSTANCE_LOCK_TTL, nx=True
            )
        except Exception as e:
            LOGGER.warning("Instance lock acquire failed (%s); proceeding without lock.", e)
            return True
        if owned:
            run_background_task(_refresh_instance_lock(), name="instance-lock-refresh")
            return True
        owner = None
        try:
            owner = await redis_client.get(_INSTANCE_LOCK_KEY)
        except Exception:
            pass
        if asyncio.get_running_loop().time() >= deadline:
            LOGGER.critical(
                "Another instance (%s) still holds the session lock after %ss. "
                "Refusing to start to avoid MTProto session corruption.",
                owner, _INSTANCE_LOCK_WAIT_TIMEOUT,
            )
            status["startup"] = "refused:lock_held"
            return False
        LOGGER.warning(
            "Session lock held by %s; retrying in %ss (old instance may be draining)...",
            owner, _INSTANCE_LOCK_RETRY_INTERVAL,
        )
        await asyncio.sleep(_INSTANCE_LOCK_RETRY_INTERVAL)


async def _refresh_instance_lock():
    from backend.database import r as redis_client
    while True:
        await asyncio.sleep(_INSTANCE_LOCK_TTL // 2)
        try:
            if redis_client:
                # XX: extend only while we still own the lock.
                held = await redis_client.set(
                    _INSTANCE_LOCK_KEY, _INSTANCE_ID, ex=_INSTANCE_LOCK_TTL, xx=True
                )
                if not held:
                    LOGGER.critical(
                        "Single-instance lock lost (expired or taken by another "
                        "process). This process may now share an MTProto session "
                        "with another instance."
                    )
                    return
        except Exception:
            pass


async def _release_instance_lock():
    from backend.database import r as redis_client
    if not redis_client:
        return
    try:
        # Compare-and-delete: only remove the lock if we still own it.
        await redis_client.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then "
            "return redis.call('del', KEYS[1]) else return 0 end",
            1,
            _INSTANCE_LOCK_KEY,
            _INSTANCE_ID,
        )
    except Exception:
        pass


def _get_start_lock():
    global _START_LOCK
    if _START_LOCK is None:
        _START_LOCK = asyncio.Lock()
    return _START_LOCK


async def _load_sudo_users(status: dict):
    from backend.core.roles import MODERATOR_ROLE, normalize_role
    from backend.database import sudo_collection

    cursor = sudo_collection.find({})
    db_sudos = await cursor.to_list(length=None)

    loaded_count = 0
    for s in db_sudos:
        try:
            user_id = int(s.get("user_id"))
        except (TypeError, ValueError):
            continue
        role = normalize_role(s.get("role")) or MODERATOR_ROLE
        sudo_roles[user_id] = role
        loaded_count += 1
        if role == MODERATOR_ROLE and user_id not in sudo_users:
            sudo_users.append(user_id)
        elif role != MODERATOR_ROLE and user_id in sudo_users:
            sudo_users.remove(user_id)

    status["sudo_users"] = f"loaded:{loaded_count}"
    if loaded_count > 0:
        LOGGER.info("Loaded %s sudo role(s) from database.", loaded_count)


async def _bootstrap_infrastructure(status: dict):
    from backend.database import r as redis_client
    from backend.database import seal_db

    await seal_db.ping()
    status["mongo"] = "connected"
    LOGGER.info("MongoDB connectivity verified.")

    if redis_client:
        try:
            await redis_client.ping()
            status["redis"] = "connected"
            LOGGER.info("Redis connectivity verified.")
        except Exception as e:
            status["redis"] = f"degraded:{type(e).__name__}"
            LOGGER.warning("Redis ping failed; Redis-backed features will use fallbacks where available: %s", e)
    else:
        status["redis"] = "disabled"

    await seal_db.ensure_indexes()
    status["indexes"] = "ensured"

    from backend.core.rarities import load_rarities
    rarity_count = await load_rarities()
    status["rarities"] = f"loaded:{rarity_count}"

    from backend.core.pets import seed_pet_catalog
    await seed_pet_catalog()
    status["pet_catalog"] = "seeded"


def _rebind_clients_to_current_loop():
    loop = asyncio.get_running_loop()
    for bot in (app, game_bot, userbot):
        if not bot:
            continue
        bot.loop = loop
        if hasattr(bot, "dispatcher"):
            bot.dispatcher.loop = loop


def _bot_status(bot, *, state: str) -> dict:
    if not bot:
        return {"state": "disabled"}
    return {
        "state": state,
        "username": getattr(bot, "username", None),
        "id": getattr(bot, "bot_id", None),
        "commands_synced": getattr(bot, "commands_synced", False),
        "command_sync_error": getattr(bot, "command_sync_error", None),
        "modules_loaded": len(getattr(bot, "loaded_modules", []) or []),
        "modules_failed": getattr(bot, "failed_modules", []) or [],
    }


async def _notify_startup(status: dict):
    from backend.core.startup import send_startup_report
    from config import config

    if not getattr(app, "is_connected", False):
        return
    try:
        module_count = len(getattr(app, "loaded_modules", []) or [])
        await send_startup_report(app, config.LOG_GROUP_ID, module_count, startup_status=status)
    except Exception as e:
        LOGGER.warning("Failed to send startup report: %s", e)


async def _stop_started_bots(started_bots):

    for bot in reversed(started_bots):
        try:
            if bot and getattr(bot, "is_connected", False):
                await bot.stop()
        except Exception as e:
            LOGGER.warning("Failed to stop %s after startup failure: %s", getattr(bot, "name", type(bot).__name__), e)


async def _cleanup_startup_failure(started_bots):
    from backend.core.resources import stop_resource_monitor
    from backend.core.tasks import cancel_background_tasks

    await stop_resource_monitor()
    await cancel_background_tasks()
    await _stop_started_bots(started_bots)


async def start_bots():
    global IS_STARTED, STARTUP_STATE
    async with _get_start_lock():
        if IS_STARTED:
            return


        STARTUP_STATE = "starting"
        started_bots = []
        status = {
            "startup": "starting",
            "sudo_users": "pending",
            "mongo": "pending",
            "redis": "pending",
            "indexes": "pending",
            "rarities": "pending",
            "pet_catalog": "pending",
            "main_bot": {"state": "pending"},
            "game_bot": {"state": "pending"},
            "userbot": {"state": "disabled" if not userbot else "pending"},
            "resource_monitor": "pending",
        }

        if not await _acquire_instance_lock(status):
            IS_STARTED = False
            STARTUP_STATE = "refused"
            # Hard-exit: a mere exception would leave a zombie web-only
            # container passing health checks while the bot is dead.
            LOGGER.critical(
                "Single-instance lock is held by another process; refusing to "
                "start. Exiting so the platform restarts this container."
            )
            os._exit(1)

        try:
            try:
                await _load_sudo_users(status)
            except Exception as e:
                status["sudo_users"] = f"failed:{type(e).__name__}"
                LOGGER.error("Failed to load sudo users from DB: %s", e)

            await _bootstrap_infrastructure(status)
            _rebind_clients_to_current_loop()

            await app.start()
            started_bots.append(app)
            status["main_bot"] = _bot_status(app, state="started")

            await game_bot.start()
            started_bots.append(game_bot)
            status["game_bot"] = _bot_status(game_bot, state="started")

            if userbot:
                from pyrogram.errors import (
                    AuthKeyDuplicated,
                    AuthKeyInvalid,
                    AuthKeyUnregistered,
                    Unauthorized,
                )
                try:
                    await userbot.start()
                    started_bots.append(userbot)
                    status["userbot"] = _bot_status(userbot, state="started")
                except (AuthKeyInvalid, AuthKeyDuplicated, AuthKeyUnregistered, Unauthorized) as e:
                    status["userbot"] = {"state": "degraded", "error": f"{type(e).__name__}: {e}"}
                    LOGGER.warning("UserBot failed to start (Auth Issue): %s", e)
                    LOGGER.warning("Scraper features will be disabled until STRING_SESSION is updated.")
                except Exception as e:
                    status["userbot"] = {"state": "degraded", "error": f"{type(e).__name__}: {e}"}
                    if "AuthKeyNotFound" in type(e).__name__ or "Auth key not found" in str(e):
                        LOGGER.warning("UserBot failed to start (Session Not Found): %s", e)
                        LOGGER.warning("Scraper features will be disabled until a valid STRING_SESSION is added.")
                    else:
                        LOGGER.error("UserBot failed to start (Unexpected): %s", e)

            from backend.core.resources import start_resource_monitor
            start_resource_monitor()
            status["resource_monitor"] = "started"
            status["startup"] = "operational"

            await _notify_startup(status)
            IS_STARTED = True
            STARTUP_STATE = "started"
        except AttributeError as e:
            if "API key is required" in str(e):
                LOGGER.critical("CRITICAL: API_ID and API_HASH are missing or invalid in environment variables!")
                LOGGER.critical("Please set API_ID and API_HASH to start the bot.")
            status["startup"] = f"failed:{type(e).__name__}"
            await _notify_startup(status)
            await _cleanup_startup_failure(started_bots)
            IS_STARTED = False
            STARTUP_STATE = "failed"
            raise
        except Exception as e:
            status["startup"] = f"failed:{type(e).__name__}"
            await _notify_startup(status)
            await _cleanup_startup_failure(started_bots)
            IS_STARTED = False
            STARTUP_STATE = "failed"
            raise


async def stop_bots():
    global IS_STARTED, STARTUP_STATE
    from backend.core.resources import stop_resource_monitor
    from backend.core.tasks import cancel_background_tasks
    from backend.database import close_connections

    await stop_resource_monitor()
    await cancel_background_tasks()
    try:
        from backend.core.spawns import flush_message_counts_to_db, flush_pending_message_increments
        await flush_pending_message_increments()
        await flush_message_counts_to_db()
    except Exception as e:
        LOGGER.warning(f"Failed to flush message counts before shutdown: {e}")

    for bot in (app, game_bot, userbot):
        if not bot:
            continue
        try:
            if getattr(bot, "is_connected", False):
                await bot.stop()
        except Exception as e:
            LOGGER.warning(f"Failed to stop {getattr(bot, 'name', type(bot).__name__)} cleanly: {e}")
    await _release_instance_lock()
    await close_connections()
    IS_STARTED = False
    STARTUP_STATE = "stopped"
