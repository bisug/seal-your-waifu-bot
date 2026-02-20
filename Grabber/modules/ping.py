from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
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
    sent_msg = await message.reply_text("**⚡ Pinging...**", parse_mode=ParseMode.MARKDOWN)
    
                 
    end_time = time.time()
    msg_ping = (end_time - start_time) * 1000
    
                
    db_start = time.time()
    await db.command("ping")
    db_end = time.time()
    db_ping = (db_end - db_start) * 1000
    
                  
    uptime = get_readable_time(time.time() - StartTime)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    proc = psutil.Process(os.getpid())
    proc_mem = proc.memory_info().rss / 1024 / 1024      
    threads = proc.num_threads()
    
    caption = (
        f"**🚀 System Status**\n\n"
        f"**📡 Ping:** `{msg_ping:.2f} ms`\n"
        f"**🗄️ DB Latency:** `{db_ping:.2f} ms`\n"
        f"**⏳ Uptime:** `{uptime}`\n\n"
        f"**🧠 RAM:** `{ram.percent}%` {status_emoji(ram.percent)}\n"
        f"**🖥️ CPU:** `{cpu}%` {status_emoji(cpu)}\n\n"
        f"**⚙️ Bot Memory:** `{proc_mem:.2f} MB`\n"
        f"**🧵 Threads:** `{threads}`\n\n"
        f"**🧰 OS:** `{platform.system()} {platform.release()}`\n"
        f"**🐍 Python:** `{platform.python_version()}`"
    )
    
    await sent_msg.edit_text(caption, parse_mode=ParseMode.MARKDOWN)
