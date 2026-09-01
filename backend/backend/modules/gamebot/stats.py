from pyrogram import enums, filters, types

from backend.client import game_bot
from backend.core.utils import html_escape
from backend.database import sessions_collection, user_collection


@game_bot.on_message(filters.command(["top", "stats"]))
async def gamebot_stats_handler(_, message: types.Message):
    stats = await sessions_collection.find_one({"id": "gamebot_global_stats"}) or {}
    name_stats = await sessions_collection.find_one({"id": "nguess_global_stats"}) or {}

    pipeline = [
        {
            "$addFields": {
                "gamebot_score": {
                    "$ifNull": ["$gamebot_wins", "$guess_count"]
                }
            }
        },
        {"$match": {"gamebot_score": {"$gt": 0}}},
        {"$sort": {"gamebot_score": -1, "balance": -1}},
        {"$limit": 10},
        {
            "$project": {
                "first_name": 1,
                "username": 1,
                "gamebot_score": 1,
                "guess_count": 1,
                "quiz_count": 1,
                "scramble_count": 1,
            }
        },
    ]
    cursor = await user_collection.aggregate(pipeline)
    users = await cursor.to_list(length=10)

    lines = ["<b>GameBot Stats</b>", ""]
    lines.append(f"<b>Name guesses:</b> <code>{int(name_stats.get('total_guesses', 0) or 0):,}</code>")
    lines.append(f"<b>Quiz wins:</b> <code>{int(stats.get('quiz_wins', 0) or 0):,}</code>")
    lines.append(f"<b>Scramble wins:</b> <code>{int(stats.get('scramble_wins', 0) or 0):,}</code>")
    lines.append(f"<b>Rewards paid:</b> <code>{int(stats.get('total_rewards', 0) or 0):,}</code> Shards")
    lines.append("")
    lines.append("<b>Top Players</b>")

    if not users:
        lines.append("<i>No GameBot wins tracked yet.</i>")
    for index, user in enumerate(users, 1):
        name = user.get("first_name") or user.get("username") or "User"
        wins = int(user.get("gamebot_score", 0) or 0)
        guesses = int(user.get("guess_count", 0) or 0)
        quizzes = int(user.get("quiz_count", 0) or 0)
        scrambles = int(user.get("scramble_count", 0) or 0)
        lines.append(
            f"{index}. <b>{html_escape(name)}</b> - <code>{wins:,}</code> wins "
            f"(G {guesses:,} / Q {quizzes:,} / S {scrambles:,})"
        )

    await game_bot.send_message_safe(
        message.chat.id,
        "\n".join(lines),
        parse_mode=enums.ParseMode.HTML,
        reply_parameters=types.ReplyParameters(message_id=message.id),
    )
