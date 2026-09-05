"""One-shot MongoDB data hygiene cleanup (2026-09 audit).

Fixes:
1. Delete user docs with no `id` field (legacy upserts; unreachable by any query).
2. Delete sessions with no `expires_at_dt` (never expire via TTL).
3. Drop orphan collections with zero code references:
   - user_characters (old schema, 3.5k dead docs)
   - scraped_characters (scraper removed in 6ade159)
   - nguess_enabled_groups (empty, unreferenced)

Idempotent: safe to re-run. Prints a report and exits non-zero only on errors.
"""
import asyncio
import sys

sys.path.insert(0, ".")


async def main() -> None:
    from backend.database import seal_db

    await seal_db.ping()
    db = seal_db.db
    report: list[str] = []

    # 1. Orphan user docs (no `id` field)
    users = db["user_collectionsss"]
    res = await users.delete_many({"id": {"$exists": False}})
    report.append(f"users without id deleted: {res.deleted_count}")

    # 2. Sessions that never expire
    sessions = db["active_sessions"]
    res = await sessions.delete_many({"expires_at_dt": {"$exists": False}})
    report.append(f"sessions without expires_at_dt deleted: {res.deleted_count}")

    # 3. Orphan collections
    names = await db.list_collection_names()
    for cname in ("user_characters", "scraped_characters", "nguess_enabled_groups"):
        if cname in names:
            await db[cname].drop()
            report.append(f"dropped collection: {cname}")
        else:
            report.append(f"already absent: {cname}")

    for line in report:
        print(line)

    # Post-conditions
    assert await users.count_documents({"id": {"$exists": False}}) == 0
    assert await sessions.count_documents({"expires_at_dt": {"$exists": False}}) == 0
    names_after = await db.list_collection_names()
    assert not {"user_characters", "scraped_characters", "nguess_enabled_groups"} & set(names_after)
    print("POST-CONDITIONS OK")


if __name__ == "__main__":
    asyncio.run(main())
