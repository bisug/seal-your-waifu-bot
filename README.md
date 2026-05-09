<div align="center">
  <img src="https://files.catbox.moe/2hsawz.jpg" alt="Seal Bot Banner" width="800">

# 🦭 Seal-Bot-V2

### The Ultimate Anime Character Collection (Waifu Grabber) Bot
#### Now with Unified Web Service & Premium React Mini App UI

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-Cloud-red?logo=redis&logoColor=white)](https://redis.io/)

[Support Group](https://t.me/seal_Your_WH_Group) • [Updates Channel](https://t.me/SEAL_UPDATE)

</div>

---

## 🌟 Overview

**Seal-Bot-V2** is a modular, high-performance Telegram bot ecosystem. It combines a robust **Pyrogram (Kurigram)** character collection game with a premium **React + Vite** powered Telegram WebApp (TWA).

This version introduces a **Unified Web Service** architecture—the Bot and the WebApp run in a single process, sharing memory and utilizing an asynchronous backend for maximum efficiency and speed.

## ✨ Key Features

- 🎮 **Dynamic Spawning**: Characters appear automatically based on group activity and message frequency.
- 📱 **Premium React TWA**: A state-of-the-art Mini App built with React 19 and Vite 6, featuring smooth animations, haptic feedback, and a native mobile feel.
- 🚀 **Unified Architecture**: Single-process deployment—Hypercorn manages both the API server and the Telegram client.
- 📊 **Performance Driven**:
  - **Denormalized Storage**: Optimized `char_count` and metrics for O(1) leaderboard lookups.
  - **Global Caching**: Redis-backed leaderboards and session management.
  - **Database Indexing**: Advanced MongoDB compound indexes for ultra-fast harem filtering.
- 🛡️ **Hardened Security**: Pre-configured Content Security Policy (CSP), GZip compression, and secure API obfuscation.
- 🦋 **Modular Logic**: Clean, separated modules for collection, trading, hunting, and hatching.

## 🛠️ Tech Stack

- **Backend**: Python 3.13+, FastAPI (API), Kurigram (Telegram Framework)
- **Frontend**: React 19, Vite 6, CSS-in-JS (Modern Aesthetics)
- **Database**: MongoDB (PyMongo Async), Redis (Caching Layer)
- **Infrastructure**: Docker Ready, Heroku/Render optimized (Procfile included)

## 🚀 Deployment

### Unified Web Service (Recommended)
This bot is designed to run as a single `web` process, removing the need for separate worker dynos.

#### Heroku / Render / VPS
1. **Build Frontend**: Run `npm run build` inside the `frontend` directory. The build artifacts will be placed in `Grabber/static`.
2. **Setup Env**: Copy `sample.env` to `.env` and fill in your credentials.
3. **Start Service**:
   ```bash
   hypercorn Grabber.webapp.main:app --bind 0.0.0.0:$PORT
   ```

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
| `WEB_APP_URL`| Domain URL for the WebApp        | Required |

## 🕹️ Commands

- `/start` - Launch the bot and access the main menu.
- `/profile` - Open the React WebApp to view your dashboard.
- `/harem` / `/collection` - Browse your caught characters.
- `/hunt` / `/hatch` - Mechanics for obtaining rare characters via eggs.
- `/status` - Diagnostics for bot latency and server health.

---

<div align="center">
  Built with ❤️ by the Seal-Bot Team
</div>

