import time
from pyrogram import filters, types
from Grabber import app, sudo_users

@app.on_message(filters.command("ping"))
async def ping(_, message: types.Message) -> None:
    if message.from_user.id not in sudo_users:
        # Check integer comparison
        if str(message.from_user.id) not in [str(x) for x in sudo_users]:
            await message.reply_text("Nouu.. its Sudo user's Command..")
            return
            
    start_time = time.time()
    sent_msg = await message.reply_text('Pong!')
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 2)
    await sent_msg.edit_text(f'Pong! {elapsed_time}ms')
