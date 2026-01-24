import time
import psutil
import platform
import os
from pyrogram import filters, types
from Grabber import app, StartTime, db

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

def status_emoji(percent):
    if percent < 40:
        return "🟢"
    elif percent < 75:
        return "🟡"
    else:
        return "🔴"

@app.on_message(filters.command("ping"))
async def ping(_, message: types.Message) -> None:
    start_time = time.time()
    sent_msg = await message.reply_text("<b>⚡ Pinging...</b>", parse_mode=enums.ParseMode.HTML)
    
    # Bot Latency
    end_time = time.time()
    msg_ping = (end_time - start_time) * 1000
    
    # DB Latency
    db_start = time.time()
    await db.command("ping")
    db_end = time.time()
    db_ping = (db_end - db_start) * 1000
    
    # System Stats
    uptime = get_readable_time(time.time() - StartTime)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    proc = psutil.Process(os.getpid())
    proc_mem = proc.memory_info().rss / 1024 / 1024  # MB
    threads = proc.num_threads()
    
    caption = (
        f"<b>🚀 System Status</b>\n\n"
        f"<b>📡 Ping:</b> <code>{msg_ping:.2f} ms</code>\n"
        f"<b>🗄️ DB Latency:</b> <code>{db_ping:.2f} ms</code>\n"
        f"<b>⏳ Uptime:</b> <code>{uptime}</code>\n\n"
        f"<b>🧠 RAM:</b> <code>{ram.percent}%</code> {status_emoji(ram.percent)}\n"
        f"<b>🖥️ CPU:</b> <code>{cpu}%</code> {status_emoji(cpu)}\n\n"
        f"<b>⚙️ Bot Memory:</b> <code>{proc_mem:.2f} MB</code>\n"
        f"<b>🧵 Threads:</b> <code>{threads}</code>\n\n"
        f"<b>🧰 OS:</b> <code>{platform.system()} {platform.release()}</code>\n"
        f"<b>🐍 Python:</b> <code>{platform.python_version()}</code>"
    )
    
    await sent_msg.edit_text(caption, parse_mode=enums.ParseMode.HTML)
