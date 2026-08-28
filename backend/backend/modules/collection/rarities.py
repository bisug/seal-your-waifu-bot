from pyrogram import enums, filters, types

from backend import app
from backend.core.rarities import (
    ACTIVE_SPAWN_RARITY_WEIGHTS,
    RARITY_MAP,
    SHOP_RARITY_WEIGHTS,  # noqa: F401  (re-exported for economy/shop.py)
    SPAWN_RARITY_WEIGHTS,
)
from backend.core.utils import handle_errors, html_escape
from backend.database import collection

# Rarity config now lives in the `rarities` collection (see core/rarities.py).
# The names below are re-exported for backward compatibility; they are the
# same live dicts, so edits via /rarityset apply everywhere.
RARITY_WEIGHTS = SPAWN_RARITY_WEIGHTS
ACTIVE_RARITY_WEIGHTS = ACTIVE_SPAWN_RARITY_WEIGHTS
@app.on_message(filters.command(["rarities", "rarity", "rlist"]))
@handle_errors
async def rarities_handler(_, message: types.Message):
    rarity_counts = {}
    total_characters = 0

    # Count per rarity with an indexed $group instead of scanning every
    # character document. Returns one row per rarity (~25) regardless of
    # collection size, so this stays fast as the archive grows. The previous
    # full find() pulled all docs to Python and could exceed socketTimeoutMS.
    cursor = await collection.aggregate(
        [{"$group": {"_id": "$rarity", "count": {"$sum": 1}}}]
    )
    async for doc in cursor:
        rarity = doc.get("_id") or "Unknown"
        count = doc.get("count") or 0
        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + count
        total_characters += count

    if not rarity_counts:
        return await message.reply_text("<b>No characters found in database.</b>", parse_mode=enums.ParseMode.HTML)

    lines = ["<b>Character Counts by Rarity:</b>", ""]

    # We display based on what's in the database, but prioritized by RARITY_MAP order if possible
    displayed_rarities = set()

    # 1. Show standard rarities first
    for i in sorted(RARITY_MAP.keys()):
        rarity_name = RARITY_MAP[i]
        if rarity_name in rarity_counts:
            count = rarity_counts[rarity_name]
            lines.append(f"{html_escape(rarity_name)}: <code>{count}</code>")
            displayed_rarities.add(rarity_name)

    # 2. Show any remaining rarities found in DB
    remaining = False
    for r_name, count in rarity_counts.items():
        if r_name not in displayed_rarities:
            if not remaining:
                lines.extend(["", "<b>Other Rarities:</b>"])
                remaining = True
            lines.append(f"{html_escape(str(r_name))}: <code>{count}</code>")

    lines.extend(["", f"<b>Total Characters:</b> <code>{total_characters}</code>"])

    chunk = ""
    for line in lines:
        next_chunk = f"{chunk}\n{line}" if chunk else line
        if len(next_chunk) > 3500:
            await message.reply_text(chunk, parse_mode=enums.ParseMode.HTML)
            chunk = line
        else:
            chunk = next_chunk
    if chunk:
        await message.reply_text(chunk, parse_mode=enums.ParseMode.HTML)
