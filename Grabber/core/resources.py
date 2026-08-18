from __future__ import annotations

import asyncio
import gc
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import psutil

from config import config
from Grabber.core.tasks import get_background_task_stats, run_background_task

LOGGER = logging.getLogger(__name__)

_PROCESS = psutil.Process(os.getpid())
_MONITOR_TASK: asyncio.Task | None = None
_LAST_CLEANUP = 0.0


@dataclass(frozen=True)
class ResourceSnapshot:
    rss_mb: float
    vms_mb: float
    available_mb: float
    system_used_percent: float
    task_count: int
    fd_count: int | None
    soft_limit_mb: int
    hard_limit_mb: int


def _read_int_file(path: Path) -> int | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
        if not value or value == "max":
            return None
        parsed = int(value)
        if parsed <= 0 or parsed > 2**60:
            return None
        return parsed
    except (OSError, ValueError):
        return None


def _detect_cgroup_memory_limit_mb() -> int | None:
    candidates = (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    )
    for path in candidates:
        limit = _read_int_file(path)
        if limit:
            return max(1, limit // (1024 * 1024))
    return None


def _detect_process_memory_limit_mb() -> int | None:
    cgroup_limit = _detect_cgroup_memory_limit_mb()
    if cgroup_limit:
        return cgroup_limit

    if sys.platform != "win32":
        try:
            import resource

            soft_limit, _ = resource.getrlimit(resource.RLIMIT_AS)
            if 0 < soft_limit < 2**60:
                return max(1, soft_limit // (1024 * 1024))
        except (ImportError, OSError, ValueError):
            pass

    total = int(psutil.virtual_memory().total // (1024 * 1024))
    return total if total > 0 else None


def _configured_memory_limits() -> tuple[int, int]:
    soft = int(getattr(config, "RESOURCE_MEMORY_SOFT_LIMIT_MB", 0))
    hard = int(getattr(config, "RESOURCE_MEMORY_HARD_LIMIT_MB", 0))
    if soft > 0 or hard > 0:
        if soft <= 0 and hard > 0:
            soft = max(1, int(hard * 0.8))
        if hard <= 0 and soft > 0:
            hard = max(soft + 1, int(soft * 1.25))
        return soft, hard

    detected = _detect_process_memory_limit_mb()
    if not detected:
        return 0, 0
    return max(1, int(detected * 0.75)), max(1, int(detected * 0.9))


def _minimum_available_memory_mb() -> int:
    configured = int(getattr(config, "RESOURCE_MIN_AVAILABLE_MB", 0))
    if configured > 0:
        return configured
    total = int(psutil.virtual_memory().total // (1024 * 1024))
    if total <= 0:
        return 128
    return max(128, min(1024, int(total * 0.05)))


def get_resource_snapshot() -> ResourceSnapshot:
    mem = _PROCESS.memory_info()
    vm = psutil.virtual_memory()
    soft_limit, hard_limit = _configured_memory_limits()
    fd_count = None
    try:
        if hasattr(_PROCESS, "num_fds"):
            fd_count = _PROCESS.num_fds()
        elif hasattr(_PROCESS, "num_handles"):
            fd_count = _PROCESS.num_handles()
    except (psutil.Error, OSError):
        fd_count = None

    return ResourceSnapshot(
        rss_mb=round(mem.rss / 1024 / 1024, 2),
        vms_mb=round(mem.vms / 1024 / 1024, 2),
        available_mb=round(vm.available / 1024 / 1024, 2),
        system_used_percent=round(vm.percent, 2),
        task_count=int(get_background_task_stats()["active"]),
        fd_count=fd_count,
        soft_limit_mb=soft_limit,
        hard_limit_mb=hard_limit,
    )


def pressure_reason(snapshot: ResourceSnapshot | None = None) -> str | None:
    snapshot = snapshot or get_resource_snapshot()
    if snapshot.hard_limit_mb > 0 and snapshot.rss_mb >= snapshot.hard_limit_mb:
        return "hard_memory_limit"
    if snapshot.soft_limit_mb > 0 and snapshot.rss_mb >= snapshot.soft_limit_mb:
        return "soft_memory_limit"
    if snapshot.available_mb <= _minimum_available_memory_mb():
        return "low_system_memory"
    return None


async def apply_memory_pressure_cleanup(reason: str) -> dict:
    global _LAST_CLEANUP
    now = time.monotonic()
    cooldown = float(getattr(config, "RESOURCE_GC_COOLDOWN_SECONDS", 120.0))
    if now - _LAST_CLEANUP < cooldown:
        return {"skipped": True, "reason": "cooldown"}
    _LAST_CLEANUP = now

    before = get_resource_snapshot()
    deleted_redis_keys = 0
    try:
        from Grabber.core.cache import purge_volatile_redis_caches

        deleted_redis_keys = await purge_volatile_redis_caches(
            max_keys=int(getattr(config, "RESOURCE_REDIS_PURGE_BATCH_SIZE", 100))
        )
    except Exception as e:
        LOGGER.warning("Resource cleanup Redis purge failed: %s", e)

    collected = gc.collect()
    after = get_resource_snapshot()
    LOGGER.warning(
        "Resource cleanup completed: reason=%s rss=%.2fMB->%.2fMB available=%.2fMB->%.2fMB "
        "gc_collected=%s redis_keys=%s tasks=%s",
        reason,
        before.rss_mb,
        after.rss_mb,
        before.available_mb,
        after.available_mb,
        collected,
        deleted_redis_keys,
        after.task_count,
    )
    return {
        "skipped": False,
        "reason": reason,
        "before": asdict(before),
        "after": asdict(after),
        "gc_collected": collected,
        "redis_keys_deleted": deleted_redis_keys,
    }


async def _resource_monitor_loop() -> None:
    interval = max(5.0, float(getattr(config, "RESOURCE_CHECK_INTERVAL_SECONDS", 60.0)))
    soft, hard = _configured_memory_limits()
    soft_label = f"{soft}MB" if soft else "auto-disabled"
    hard_label = f"{hard}MB" if hard else "auto-disabled"
    LOGGER.info(
        "Resource monitor started: interval=%.1fs soft_limit=%s hard_limit=%s task_soft_limit=%s",
        interval,
        soft_label,
        hard_label,
        getattr(config, "RESOURCE_TASK_SOFT_LIMIT", 500),
    )
    try:
        while True:
            await asyncio.sleep(interval)
            snapshot = get_resource_snapshot()
            reason = pressure_reason(snapshot)

            task_soft_limit = int(getattr(config, "RESOURCE_TASK_SOFT_LIMIT", 500))
            if task_soft_limit > 0 and snapshot.task_count >= task_soft_limit:
                LOGGER.warning(
                    "Background task pressure: active=%s soft_limit=%s",
                    snapshot.task_count,
                    task_soft_limit,
                )

            if reason:
                if reason == "hard_memory_limit":
                    LOGGER.critical("Process memory exceeded hard limit: %s", asdict(snapshot))
                await apply_memory_pressure_cleanup(reason)
    except asyncio.CancelledError:
        LOGGER.info("Resource monitor stopped.")
        raise


def start_resource_monitor() -> asyncio.Task | None:
    global _MONITOR_TASK
    if not getattr(config, "RESOURCE_MONITOR_ENABLED", True):
        LOGGER.info("Resource monitor disabled by configuration.")
        return None
    if _MONITOR_TASK and not _MONITOR_TASK.done():
        return _MONITOR_TASK
    _MONITOR_TASK = run_background_task(_resource_monitor_loop(), name="resource-monitor")
    return _MONITOR_TASK


async def stop_resource_monitor() -> None:
    global _MONITOR_TASK
    if not _MONITOR_TASK or _MONITOR_TASK.done():
        _MONITOR_TASK = None
        return
    _MONITOR_TASK.cancel()
    try:
        await _MONITOR_TASK
    except asyncio.CancelledError:
        pass
    finally:
        _MONITOR_TASK = None
