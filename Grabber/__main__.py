import importlib
import asyncio
import re

from pyrogram import filters, types, idle
from pyrogram.handlers import MessageHandler

from Grabber import (
    app, LOGGER
)
from Grabber.modules import ALL_MODULES
from Grabber.core.message_counter import message_counter


if __name__ == "__main__":
    app.run()
