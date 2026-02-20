import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from Grabber import app, LOGGER, OWNER_ID, sudo_users
from config import config

namespaces = {}
AUTHORIZED_USERS = list(set(sudo_users + [OWNER_ID]))

def namespace_of(chat_id, message):
    if chat_id not in namespaces:
        namespaces[chat_id] = {
            "__builtins__": globals()["__builtins__"],
            "app": app,
            "message": message,
            "user": message.from_user,
            "chat": message.chat,
            "config": config,
        }
    return namespaces[chat_id]

async def send_result(result, message: types.Message):
    if not result:
        return
    
    result = str(result)
    if len(result) > 2000:
        with io.BytesIO(str.encode(result)) as out_file:
            out_file.name = "output.txt"
            await message.reply_document(document=out_file)
    else:
        await message.reply_text(f"```python\n{result}```", parse_mode=ParseMode.MARKDOWN)

def cleanup_code(code):
    if code.startswith("```") and code.endswith("```"):
        return "\n".join(code.split("\n")[1:-1])
    return code.strip("` \n")

@app.on_message(filters.command(["e", "ev", "eva", "eval", "x", "ex", "exe", "exec", "py"]) & filters.user(AUTHORIZED_USERS))
async def evaluate_or_execute(_, message: types.Message):
    content = message.text.split(None, 1)
    if len(content) < 2:
        return
    
    body = cleanup_code(content[1])
    env = namespace_of(message.chat.id, message)
    
    stdout = io.StringIO()
    to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

    try:
        exec(to_compile, env)
    except Exception as e:
        await send_result(f"{e.__class__.__name__}: {e}", message)
        return

    func = env["func"]

    try:
        with redirect_stdout(stdout):
            func_return = await func()
    except Exception as e:
        value = stdout.getvalue()
        await send_result(f"{value}{traceback.format_exc()}", message)
    else:
        value = stdout.getvalue()
        result = None
        if func_return is None:
            if value:
                result = f"{value}"
            else:
                try:
                    result = f"{repr(eval(body, env))}"
                except:
                    pass
        else:
            result = f"{value}{func_return}"
        
        if result:
            await send_result(result, message)
        elif value:
             await send_result(value, message)

@app.on_message(filters.command("clearlocals") & filters.user(AUTHORIZED_USERS))
async def clear_locals(_, message: types.Message):
    global namespaces
    if message.chat.id in namespaces:
        del namespaces[message.chat.id]
    await message.reply_text("Cleared locales for this chat.")
