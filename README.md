<div align="center">
  <img src="https://files.catbox.moe/2hsawz.jpg" alt="Seal Bot Banner" width="800">

# Seal-Bot-V2

### The Ultimate Anime Character Collection (Waifu Grabber) Bot
#### Now with Unified Web Service & Premium WebApp UI

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Kurigram](https://img.shields.io/badge/Kurigram-v2.2-orange?logo=telegram&logoColor=white)](https://pypi.org/project/Kurigram/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)](https://www.mongodb.com/)

[Support Group](https://t.me/seal_Your_WH_Group) • [Updates Channel](https://t.me/SEAL_UPDATE)

</div>

---

## Overview

**Seal-Bot-V2** is a high-performance Telegram bot ecosystem. It combines a robust **Pyrogram**-based character collection game with a premium **FastAPI**-powered WebApp. 

This version introduces a **Unified Web Service** architecture—the Bot and the WebApp run in a single process, sharing memory and resources for maximum efficiency.

---

## Project Structure

```text
Seal-Bot-V2/
├── Grabber/                # Main Application Package
│   ├── core/               # Core Game Logic & Systems
│   │   ├── cache.py        # Redis & Local Caching
│   │   ├── spawns.py       # Character Spawning Engine
│   │   ├── progression.py  # Leveling & XP System
│   │   └── sessions.py     # User Session Management
│   ├── database/           # Database Layer
│   │   ├── models.py       # MongoDB Document Schemas
│   │   └── __init__.py     # Connection Handling
│   ├── modules/            # Bot Feature Modules
│   │   ├── collection/     # Harem & Character Management
│   │   ├── economy/        # Shop, Currency & Rewards
│   │   ├── games/          # Mini-games & Interactive Features
│   │   └── social/         # Group Management & Interactions
│   ├── webapp/             # FastAPI Web Application
│   │   ├── api.py          # REST Endpoints
│   │   ├── auth.py         # Telegram WebApp Auth
│   │   └── main.py         # Web Server Entry Point
│   └── frontend/           # WebApp Static Assets (CSS/JS/HTML)
├── config.py               # Global Configuration Loader
├── Dockerfile              # Docker Container Definition
├── Procfile                # Heroku Process File
├── heroku.yml              # Heroku Container Config
├── requirements.txt        # Python Dependencies
├── sample.env              # Environment Variables Template
└── runtime.txt             # Python Runtime Specification
```

---

## Key Features & How They Work

### Character Collection Game
*   **Dynamic Spawning**: Characters appear in groups based on recent message activity. Use the guess commands to claim them!
*   **Harem Management**: View and manage your collected characters via /harem or the premium WebApp.
*   **Trading & Marketplace**: Exchange characters with other players to complete your collection.

### Premium WebApp UI
*   **Unified Access**: Open your profile directly from Telegram using /profile.
*   **Real-time Updates**: Experience smooth animations and real-time rare card glows using modern Glassmorphism CSS.
*   **Haptic Feedback**: Integrated mobile haptics for a native application feel.

### Progression & Economy
*   **Leveling System**: Earn XP through participation and level up your profile.
*   **In-game Shop**: Spend your hard-earned currency on rare eggs, boosters, and cosmetic items.
*   **Leaderboards**: Compete globally or within your group for the top collector spot.

---

## Deployment Guide

### 1. Heroku Deployment

**Method A: Procfile (Standard)**
1. Connect your GitHub repo to Heroku.
2. Set the environment variables in Settings > Config Vars.
3. Heroku will automatically detect the Procfile and start the web process.

**Method B: Docker (Container)**
1. Use the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli):
   ```bash
   heroku stack:set container
   git push heroku main
   ```

### 2. Render Deployment
1. Create a new Web Service.
2. Select **Docker** as the Runtime.
3. Render will automatically detect the **Dockerfile** in the root directory and build the image.
4. Add your .env variables in the Environment section.

### 3. Koyeb Deployment
1. Create a new App on Koyeb.
2. Select **GitHub** as the deployment method.
3. Set the **Builder** to **Docker**.
4. Koyeb will automatically detect and build using the **Dockerfile**.
5. In the Environment Variables section, add all keys from sample.env.

---

## WebApp Setup Guide

To ensure the WebApp buttons work smoothly across all Telegram platforms, follow these steps:

### 1. Set the WebApp URL
Ensure the WEB_APP_URL in your environment variables is set to your public deployment URL (e.g., https://your-app.herokuapp.com).

### 2. Configure @BotFather (Crucial for Groups)
To get a professional "Mini App" feel in groups and channels, you must register your WebApp with Telegram's BotFather:
1. Open [@BotFather](https://t.me/BotFather) and select your bot.
2. Go to **Bot Settings** > **Mini App**.
3. Enable the Mini App and provide your WEB_APP_URL.
4. **Set a Short Name**: By default, the bot uses `app`. If you choose a different name, update MINI_APP_SHORT_NAME in config.py (or set it as an env var).

### 3. Usage in Bot
The bot automatically generates buttons using:
- **Direct Buttons**: Using types.WebAppInfo for a native popup in Private Messages.
- **App Links**: Using https://t.me/bot_username/short_name for a seamless experience in groups.

---

## Environment Variables Guide

To run the bot, you need to collect several API keys and connection strings. Follow this guide to get them:

### 1. Telegram API (API_ID & API_HASH)
1.  Visit [my.telegram.org](https://my.telegram.org).
2.  Log in with your phone number.
3.  Go to **API development tools**.
4.  Create a new application (you can use any name).
5.  Copy your App api_id and App api_hash.

### 2. Bot Token (TOKEN & SUB_TOKEN)
1.  Message [@BotFather](https://t.me/BotFather) on Telegram.
2.  Use /newbot to create your main bot and get the TOKEN.
3.  Use /newbot again if you need a secondary bot for the SUB_TOKEN (used for certain mini-games).

### 3. MongoDB (MONGO_URL)
1.  Sign up for a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2.  Create a new Cluster (the Shared Tier is free).
3.  Go to **Database Access** and create a user with a password.
4.  Go to **Network Access** and add 0.0.0.0/0 (allow access from anywhere).
5.  On the Cluster Dashboard, click **Connect** > **Connect your application**.
6.  Copy the connection string and replace <password> with your user's password.

### 4. Redis via Upstash (REDIS_URL)
1.  Go to [Upstash](https://upstash.com/) and create an account.
2.  Create a new **Redis** database.
3.  Select a region close to your bot's hosting.
4.  Once created, scroll down to the **Connect** section.
5.  Select **redis-py** or copy the **URL** (it should look like rediss://default:password@host:port).

### 5. Other Required IDs
- **OWNER_ID**: Your Telegram user ID. You can get this from bots like [@userinfobot](https://t.me/userinfobot).
- **SUDO_USERS**: A comma-separated list of Telegram IDs for users who should have admin access to the bot.
- **WEB_APP_URL**: The full URL where your WebApp is hosted (e.g., https://my-seal-bot.koyeb.app).

---

## Name Guessing Game (nguess)

The bot includes an interactive "Name Guessing" mini-game designed for groups, featuring dynamic rewards and milestone bonuses.

### Mechanics
1.  **Trigger**: Use the `/nguess` command (if enabled for the group) to start.
2.  **Briefing**: The bot shows an image of a character and its source anime.
3.  **Identification**: Players name the character in the chat. The bot intelligently matches nicknames and partial names.
4.  **Continuous Play**: Once a character is correctly identified, the next game starts automatically.

### Reward System
- **Base Bounty**: 10 Shards.
- **Participation Bonus**: +5 Shards per unique player who attempted a guess.
- **Max Bounty**: Limited to 50 Shards per round.

### Global Milestones
A global counter tracks correct guesses across all authorized groups:
- **50th Guesser**: Wins a **500 Shard** bonus.
- **100th Guesser**: Wins a **1,000 Shard** bonus.

### Administrative Controls
Only Sudo users and the Owner can manage where the game runs:
- `/ngon`: Authorize the current sector (group) for the guessing game.
- `/ngoff`: Revoke authorization for the current sector.
- `/nglist`: List all currently authorized sectors.

---

## Bot Commands

The bot provides a variety of commands for players and administrators.

### User Commands

| Command | Description |
| :--- | :--- |
| `/start` | Start the bot and get the main menu |
| `/help` | Display help information and command list |
| `/seal [name]` | Attempt to collect a character that has spawned |
| `/harem` | Open your character collection (Legacy text-based) |
| `/balance` | Check your current currency (Shards and Zenith) |
| `/daily` | Claim your daily reward |
| `/shop` | Open the server-side shop for characters and pets |
| `/hunt` | Go on a hunt to find items or characters |
| `/guess` | Play the character name guessing game |
| `/quests` | View and claim rewards for daily/weekly quests |
| `/pet` | Manage your pets and view their status |
| `/profile` | View your comprehensive profile stats |
| `/leaderboard` | View global rankings (harem, level, currency) |
| `/trade [reply]` | Initiate a trade with another user |
| `/propose [reply]` | Propose to another user to become partners |

### Admin & Owner Commands

| Command | Description |
| :--- | :--- |
| `/upload` | Add new characters to the database |
| `/delete [id]` | Remove a character from the database and logs |
| `/broadcast` | Send a message to all users and chats |
| `/sudo [add/rm]` | Manage sudo users for the bot |
| `/check [id]` | Check a user's detailed information and stats |
| `/sp_config` | Configure chat-specific spawn frequencies |
| `/giveaway` | Start a global or chat-specific giveaway |
| `/eval [code]` | Execute Python code (Owner only - High Risk) |
| `/chsearch [name]` | Efficiently search for characters in the database |

---

## WebApp & API Architecture

The bot features a high-performance, unified web service where the Telegram bot and the API server run in the same process.

### Unified Service Stack
- **Framework**: FastAPI (Asynchronous Python Framework).
- **Server**: Uvicorn (ASGI server).
- **Lifecycle**: The bot starts and stops automatically with the FastAPI application using the `@asynccontextmanager` lifespan handler.

### Security & Authentication
1.  **Handshake**: When the Mini App opens, it sends the Telegram `initData` to the `/secure_init` endpoint.
2.  **Validation**: The server validates this data using an HMAC-SHA256 hash signed with the bot's secret token.
3.  **Sessions**: Upon successful validation, a secure UUID session token is generated and stored in **Redis** (with MongoDB as a fallback).
4.  **Authorization**: Subsequent requests use a `Bearer` token in the Authorization header.
5.  **Rate Limiting**: To prevent abuse, the API implements a sliding window rate limit (default: 30 requests per minute per user).

### Core API Endpoints
- `/api/me`: Comprehensive profile data including level, XP, balance, and active pets.
- `/api/harem`: Efficiently Retrieves the user's collection with pagination and search support.
- `/api/leaderboard`: Global rankings for harem size, level, and currency, cached for performance.
- `/api/shop`: Server-side management of character stock and pet purchases.

---

## Dockerfile Architecture

The project's `Dockerfile` is optimized for security and image size using a multi-stage build process.

### Stage 1: Builder
- **Base Image**: `python:3.13-slim`.
- **Function**: Installs necessary build dependencies (`build-essential`, `libffi-dev`, `libssl-dev`) that are required to compile certain Python packages but are not needed at runtime.
- **Outcome**: It builds Python "wheels" for all dependencies in `requirements.txt`, which are then passed to the next stage.

### Stage 2: Final
- **Base Image**: `python:3.13-slim` (fresh and clean).
- **Security**: Creates a non-root user (`botuser`) with UID 1000 to run the application, adhering to the principle of least privilege.
- **Optimization**: Only the pre-compiled wheels and the application code are copied from the builder stage. This keeps the final image lightweight and free of unnecessary build tools.
- **Execution**: The container defaults to running `python -m Grabber`, which initializes the unified web service (Bot + FastAPI).

> [!IMPORTANT]
> When deploying via Docker, ensure all environment variables from `sample.env` are passed to the container during runtime.

---

## Character Upload Guide

For administrators and sudo users, adding new characters to the database is streamlined through the bot.

### How to Upload
1.  **Format 1 (Reply)**: Reply to an image or document with:
    `/upload character-name anime-name rarity-number`
2.  **Format 2 (Direct)**: Send the command with an image URL:
    `/upload img_url character-name anime-name rarity-number`

> [!NOTE]
> Use hyphens `-` instead of spaces for names in the command (e.g., `muzan-kibutsuji`). The bot will automatically convert them to spaces.

### Rarity Map
When uploading, use the corresponding number for the character's rarity:

| Number | Rarity Name |
| :--- | :--- |
| 1 | Common |
| 2 | Rare |
| 3 | Legendary |
| 4 | Medium |
| 5 | Cosmic |
| 6 | Exclusive |
| 7 | Limited Edition |
| 8 | Shop |
| 9 | Royal |
| 10 | Antique |

### Storage Flow
- The bot first attempts to host the image on **Catbox**.
- If Catbox fails, it uses **ImgBB** as a backup.
- Once hosted, the character is sent to the designated **Logs Channel** and added to the MongoDB collection.

---

## Database Structure

The project uses MongoDB for data persistence. Below is the detailed structure of the primary collections:

### 1. Users Collection
Stores user profile information, inventory, and progression stats.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Telegram User ID (Primary Key) |
| `first_name` | String | User's first name |
| `username` | String | Telegram username (optional) |
| `balance` | Integer | In-game currency balance |
| `zenith` | Integer | Premium currency balance |
| `characters` | List | Array of owned characters/cards |
| `xp` / `level` | Integer | Progression and leveling data |
| `daily_streak` | Integer | Consecutive days active |
| `pass_type` | String | Subscription tier (free, premium, elite) |

### 2. Characters Collection
Stores the master list of all characters available in the game.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique character identifier |
| `name` | String | Name of the character |
| `anime` | String | Source anime/series name |
| `rarity` | String | Character rarity tier |
| `img_url` | String | Link to the character image |
| `zenith_price` | Integer | Cost in premium currency |
| `sold_count` | Integer | Number of times this character was claimed |

---

## Cache Architecture

The project uses Redis as a high-performance caching layer to reduce MongoDB load and improve response times for frequently accessed data and transient states.

### 1. Implementation (`Grabber/core/cache.py`)
All cache operations are wrapped in safe-by-default helpers. If Redis is unavailable or fails, the system automatically falls back to MongoDB for persistent data or proceeds without caching for transient states.

### 2. Key Prefixes & TTLs
Data is partitioned using specific key prefixes with defined Time To Live (TTL) values.

| Prefix | Data Type | TTL | Description |
| :--- | :--- | :--- | :--- |
| `user:{id}` | JSON | 5m | Cached full user document |
| `balance:{id}` | Int | 5m | Cached shard balance for quick lookups |
| `cooldown:{key}` | Float | Variable | Command cooldown timestamps |
| `lb:{metric}` | JSON | 5m | Cached leaderboard rankings |
| `session:{id}` | JSON | 1h | WebApp session data (MongoDB fallback) |
| `nguess_groups` | Set | 10m | Set of IDs for groups with guessing enabled |
| `daily:{id}` | String | 48h | Last claim date for daily rewards |
| `weekly:{id}` | String | 8d | Last claim date for weekly rewards |

### 3. Fallback & Consistency
- **Session Management**: Sessions are tried in Redis first for speed. If empty, the system queries MongoDB and re-caches the result.
- **Cache Invalidation**: The `invalidate_user_cache` and `invalidate_leaderboard_cache` functions are called after write operations to ensure stale data is never served.
- **Atomicity**: Features like command cooldowns use Redis `SET NX EX` to ensure atomic check-and-set operations across multiple bot instances.

---

## Rarity Extension Guide

Adding new rarities requires updates in two main locations to ensure they are registered and correctly balanced in the spawn engine.

### Step 1: Register the Rarity
Open `Grabber/modules/collection/rarities.py` and add your new rarity to the `RARITY_MAP`. 
- Assign a unique number (11, 12, etc.).
- Use a distinct emoji and name.
```python
RARITY_MAP = {
    ...
    11: "🌟 Mystical"
}
```

### Step 2: Configure Spawn Weights
In the same file, add your new rarity to the weight dictionaries to enable it for natural spawns:
- `RARITY_WEIGHTS`: Standard message-based spawns.
- `ACTIVE_RARITY_WEIGHTS`: Used when chat activity is high (10+ active users).

> [!TIP]
> The weights are relative. If "Common" is 50 and "Mystical" is 1, it means Common is 50x more likely to appear.

### Step 3: Set Milestones (Optional)
If you want the rarity to appear at specific message counts (e.g., every 500th message), update `special_rarity_thresholds` in `Grabber/core/message_counter.py`.

### Step 4: Uploading Characters
Once registered, you can immediately start uploading characters with the new rarity using the assigned number:
`/upload name anime 11`

---

## Configuration

| Variable | Description |
| :--- | :--- |
| `TOKEN` | Main Telegram Bot Token |
| `API_ID` / `API_HASH` | Telegram API Credentials from [my.telegram.org](https://my.telegram.org) |
| `MONGO_URL` | MongoDB Connection String (Atlas recommended) |
| `REDIS_URL` | Redis Connection String for caching |
| `WEB_APP_URL` | Public URL where your WebApp is hosted |

> [!TIP]
> Always use sample.env as a template for your environment variables to ensure compatibility.

---

<div align="center">
  Built with love by the Seal-Bot Team
</div>
