<div align="center">
  <img src="https://files.catbox.moe/2hsawz.jpg" alt="Seal Bot Banner" width="800">

# 🦭 Seal-Bot-V2

### The Ultimate Anime Character Collection (Waifu Grabber) Bot
#### Now with Unified Web Service & Premium WebApp UI

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Kurigram](https://img.shields.io/badge/Kurigram-v2.2-orange?logo=telegram&logoColor=white)](https://pypi.org/project/Kurigram/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)](https://www.mongodb.com/)

[Support Group](https://t.me/seal_Your_WH_Group) • [Updates Channel](https://t.me/SEAL_UPDATE)

</div>

---

## 🌟 Overview

**Seal-Bot-V2** is a high-performance Telegram bot ecosystem. It combines a robust **Pyrogram**-based character collection game with a premium **FastAPI**-powered WebApp. 

This version introduces a **Unified Web Service** architecture—the Bot and the WebApp run in a single process, sharing memory and resources for maximum efficiency.

## ✨ Key Features

- 🎮 **Dynamic Spawning**: Characters appear automatically based on message frequency.
- 📱 **Premium WebApp**: Native-feel UI with haptic feedback, swipe gestures, and real-time rare card glows.
- 🚀 **Unified Architecture**: One process runs both the Telegram bot and the API server.
- 🛡️ **Hardened Security**: Built-in Content Security Policy (CSP), GZip compression, and secure API headers.
- 🖼️ **Robust Rendering**: Smart image fallback system—no more broken avatars or empty shop cards.
- 🦋 **Modular Frontend**: Organized template-based structure for easy customization and maintenance.
- 📊 **Optimized Backend**: Advanced MongoDB compound indexes for lightning-fast leaderboard and harem browsing.

## 🛠️ Tech Stack

- **Backend**: Python 3.13+, FastAPI, Pyrogram (Kurigram)
- **Frontend**: Vanilla JS (Native Mobile Optimized), Glassmorphism CSS
- **Database**: MongoDB (Motor), Redis (Caching)
- **Infrastructure**: Heroku/Docker

## 🚀 Deployment

### Unified Web Service (Recommended)
This bot is designed to run as a single `web` process.

#### Heroku / Render
The `Procfile` is pre-configured to start the bot and web service together:
```text
web: hypercorn Grabber.webapp.main:app --bind 0.0.0.0:$PORT
```
1. Deploy to your platform of choice.
2. Set all required environment variables (see `sample.env`).
3. Scale the `web` process to 1. **No separate worker is needed.**



## ⚙️ Configuration

| Variable     | Description                      | Default  |
| ------------ | -------------------------------- | -------- |
| `TOKEN`      | Main Telegram Bot Token          | Required |
| `SUB_TOKEN`  | Secondary Bot Token (Nguess)     | Required |
| `API_ID`     | Telegram API ID                  | Required |
| `API_HASH`   | Telegram API Hash                | Required |
| `MONGO_URL`  | MongoDB Connection URI           | Required |
| `REDIS_URL`  | Redis Connection URI             | Required |
| `OWNER_ID`   | Telegram ID of the bot owner     | Required |
| `SUDO_USERS` | Comma-separated list of sudo IDs | Optional |

## 🦋 Collection & Commands

- `/start` - Start the bot.
- `/profile` - View your native profile webapp.
- `/harem` - View your collection.
- `/hunt` / `/hatch` - Hunt for rare eggs and hatch them.
- `/status` - Check bot latency and shard info.

---

<div align="center">
  Built with ❤️ by the Seal-Bot Team
</div>
