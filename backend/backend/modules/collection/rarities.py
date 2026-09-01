"""Character counts by rarity.

Reads one row per rarity from an indexed $group aggregation (never scans
all character docs to Python), sorts by the canonical rarity_id order from
the `rarities` collection, and shows each tier's share of the archive.

Backward-compat re-exports (same live dicts as core/rarities.py, so
/rarityset edits apply everywhere without re-imports):
    RARITY_MAP          — admin/scraper, admin/update_char, admin/upload,
                          collection/hmode, core/uploads, webapp upload route
    SHOP_RARITY_WEIGHTS — economy/shop
    RARITY_WEIGHTS / ACTIVE_RARITY_WEIGHTS — legacy aliases
"""

from pyrogram import enums, filters, types

from backend import app
from backend.core.rarities import (
    ACTIVE_SPAWN_RARITY_WEIGHTS,
    RARITY_IDS,
    RARITY_MAP,  # noqa: F401  (re-exported; see module docstring)
    SHOP_RARITY_WEIGHTS,  # noqa: F401  (re-exported for economy/shop.py)
    SPAWN_RARITY_WEIGHTS,
)
from backend.core.utils import handle_errors, html_escape
from backend.database import collection

RARITY_WEIGHTS = SPAWN_RARITY_WEIGHTS
ACTIVE_RARITY_WEIGHTS = ACTIVE_SPAWN_RARITY_WEIGHTS

# Telegram hard-caps a message at 4096 chars; stay under with headroom.
_MAX_CHUNK = 3500


async def _counts_by_rarity() -> dict[str, int]:
    """One row per rarity via server-side $group on the rarity index."""
    cursor = await collection.aggregate(
        [{"$group": {"_id": "$rarity", "count": {"$sum": 1}}}]
    )
    rows = await cursor.to_list(length=200)
    counts: dict[str, int] = {}
    for row in rows:
        label = row.get("_id") or "Unknown"
        counts[str(label)] = counts.get(label, 0) + int(row.get("count") or 0)
    return counts


def _sort_key(label: str) -> tuple[int, str]:
    """Known rarities sort by rarity_id; unknown labels sink to the end."""
    return (RARITY_IDS.get(label, 10**9), label)


def _build_lines(counts: dict[str, int]) -> list[str]:
    total = sum(counts.values())
    lines = ["<b>Character Counts by Rarity:</b>", ""]
    for label in sorted(counts, key=_sort_key):
        count = counts[label]
        share = (count / total * 100) if total else 0
        lines.append(
            f"{html_escape(label)}: <code>{count:,}</code> <i>({share:.1f}%)</i>"
        )
    lines.extend(["", f"<b>Total Characters:</b> <code>{total:,}</code>"])
    return lines


def _split_chunks(lines: list[str]) -> list[str]:
    """Pack lines into as few messages as Telegram's 4096 limit allows."""
    chunks: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > _MAX_CHUNK:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


@app.on_message(filters.command(["rarities", "rarity", "rlist"]))
@handle_errors
async def rarities_handler(_, message: types.Message):
    counts = await _counts_by_rarity()
    if not counts:
        return await message.reply_text(
            "<b>No characters found in database.</b>",
            parse_mode=enums.ParseMode.HTML,
        )
    for chunk in _split_chunks(_build_lines(counts)):
        await message.reply_text(chunk, parse_mode=enums.ParseMode.HTML)
