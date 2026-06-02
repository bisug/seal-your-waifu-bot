import os
import platform
import time
try:
    import psutil
except ModuleNotFoundError:
    psutil = None
from pyrogram import enums, errors, filters, types
from pyrogram.enums import ParseMode

from Grabber import StartTime, app, db
from Grabber.core.utils import handle_errors
from Grabber.database import collection, group_collection, user_collection

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time
def status_flag(percent):
    if percent < 40:
        return "[Optimal]"
    elif percent < 75:
        return "[Normal]"
    else:
        return "[High Load]"
@app.on_message(filters.command("ping"))
@handle_errors
async def ping(_, message: types.Message) -> None:
    start_time = time.time()
    sent_msg = await message.reply_text("<b>Pinging...</b>", parse_mode=enums.ParseMode.HTML)
    end_time = time.time()
    msg_ping = (end_time - start_time) * 1000
    db_start = time.time()
    await db.command("ping")
    db_end = time.time()
    db_ping = (db_end - db_start) * 1000
    uptime = get_readable_time(time.time() - StartTime)
    if psutil:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        proc = psutil.Process(os.getpid())
        proc_mem = proc.memory_info().rss / 1024 / 1024
        threads = proc.num_threads()
        resource_text = (
            f"<b>RAM Usage:</b> <code>{ram.percent}%</code> {status_flag(ram.percent)}\n"
            f"<b>CPU Usage:</b> <code>{cpu}%</code> {status_flag(cpu)}\n\n"
            f"<b>Bot Memory:</b> <code>{proc_mem:.2f} MB</code>\n"
            f"<b>Threads:</b> <code>{threads}</code>\n\n"
        )
    else:
        resource_text = "<b>System Metrics:</b> <code>psutil unavailable</code>\n\n"
    caption = (
        f"<b>System Status</b>\n\n"
        f"<b>Ping:</b> <code>{msg_ping:.2f} ms</code>\n"
        f"<b>DB Latency:</b> <code>{db_ping:.2f} ms</code>\n"
        f"<b>Uptime:</b> <code>{uptime}</code>\n\n"
        f"{resource_text}"
        f"<b>OS:</b> <code>{platform.system()} {platform.release()}</code>\n"
        f"<b>Python:</b> <code>{platform.python_version()}</code>"
    )
    await sent_msg.edit_text(caption, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("stats"))
@handle_errors
async def stats(_, message: types.Message) -> None:
    db_start = time.time()
    await db.command("ping")
    db_ping = (time.time() - db_start) * 1000

    total_characters = await collection.estimated_document_count()
    total_users = await user_collection.estimated_document_count()
    total_groups = await group_collection.estimated_document_count()
    uptime = get_readable_time(time.time() - StartTime)

    await message.reply_text(
        "<b>Bot Statistics</b>\n\n"
        f"<b>Characters:</b> <code>{total_characters:,}</code>\n"
        f"<b>Users:</b> <code>{total_users:,}</code>\n"
        f"<b>Groups:</b> <code>{total_groups:,}</code>\n"
        f"<b>DB Latency:</b> <code>{db_ping:.2f} ms</code>\n"
        f"<b>Uptime:</b> <code>{uptime}</code>",
        parse_mode=enums.ParseMode.HTML,
    )
