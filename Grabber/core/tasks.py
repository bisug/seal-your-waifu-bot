import asyncio
import logging
from typing import Coroutine, Set

from config import config

LOGGER = logging.getLogger(__name__)

# Maintain a strong reference to running background tasks
# to prevent garbage collection mid-execution.
_RUNNING_TASKS: Set[asyncio.Task] = set()


def _task_label(task: asyncio.Task) -> str:
    try:
        return task.get_name()
    except Exception:
        return repr(task)


def _finalize_task(task: asyncio.Task) -> None:
    _RUNNING_TASKS.discard(task)
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        LOGGER.exception("Background task failed: %s", _task_label(task))

def run_background_task(coro: Coroutine, *, name: str | None = None) -> asyncio.Task:
    """
    Spawns an async task, keeping a strong reference to prevent premature garbage collection.
    Automatically removes itself from the set when done.
    """
    task_count = len(_RUNNING_TASKS)
    soft_limit = int(getattr(config, "RESOURCE_TASK_SOFT_LIMIT", 500))
    if soft_limit > 0 and task_count >= soft_limit:
        LOGGER.warning(
            "Background task count is high: active=%s soft_limit=%s new_task=%s",
            task_count,
            soft_limit,
            name or getattr(coro, "__qualname__", type(coro).__name__),
        )
    task = asyncio.create_task(coro, name=name)
    _RUNNING_TASKS.add(task)
    task.add_done_callback(_finalize_task)
    return task


def get_background_task_stats() -> dict:
    active = [task for task in _RUNNING_TASKS if not task.done()]
    return {
        "active": len(active),
        "done_pending_finalize": len(_RUNNING_TASKS) - len(active),
        "names": sorted(_task_label(task) for task in active),
    }


async def cancel_background_tasks(timeout: float | None = None) -> None:
    current = asyncio.current_task()
    tasks = [task for task in list(_RUNNING_TASKS) if task is not current and not task.done()]
    if not tasks:
        return
    LOGGER.info("Cancelling %s background task(s).", len(tasks))
    for task in tasks:
        task.cancel()
    try:
        await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout if timeout is not None else config.RESOURCE_SHUTDOWN_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        still_running = [task for task in tasks if not task.done()]
        LOGGER.warning(
            "Timed out waiting for %s background task(s) to stop: %s",
            len(still_running),
            ", ".join(_task_label(task) for task in still_running[:10]),
        )
