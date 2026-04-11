import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    print("Importing config...")
    import config
    print("Importing Grabber...")
    import Grabber
    print("Importing sync_handler...")
    from Grabber.core import sync_handler
    print("Checking ContinuePropagation...")
    from pyrogram import ContinuePropagation
    print("SUCCESS: All imports okay.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
