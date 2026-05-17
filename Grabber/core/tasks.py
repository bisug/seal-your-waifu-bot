import asyncio
from typing import Coroutine, Set

# Maintain a strong reference to running background tasks
# to prevent garbage collection mid-execution.
_RUNNING_TASKS: Set[asyncio.Task] = set()

def run_background_task(coro: Coroutine) -> asyncio.Task:
    """
    Spawns an async task, keeping a strong reference to prevent premature garbage collection.
    Automatically removes itself from the set when done.
    """
    task = asyncio.create_task(coro)
    _RUNNING_TASKS.add(task)
    task.add_done_callback(_RUNNING_TASKS.discard)
    return task
