<div align="center">
  <img src="https://files.catbox.moe/2hsawz.jpg" alt="Seal Bot Banner" width="800">

# 🦭 Seal-Bot

### The Ultimate Anime Character Collection (Waifu Grabber) Bot

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-v2.0-orange?logo=telegram&logoColor=white)](https://docs.pyrogram.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Support Group](https://t.me/seal_Your_WH_Group) • [Updates Channel](https://t.me/SEAL_UPDATE)

</div>

---

## 🌟 Overview

**Seal-Bot** is a high-performance Telegram bot built with **Pyrogram** and **Motor** (asynchronous MongoDB). It gamifies group interactions by spawning anime characters (waifus/husbandos) based on chat activity. Users can collect, trade, and showcase their "seized" characters.

## ✨ Key Features

- 🎮 **Dynamic Spawning**: Characters appear automatically based on message frequency.
- 💎 **Rarity System**: Multiple rarity tiers:
  - ⚪ **Common**
  - 🟢 **Medium**
  - 🟠 **Rare**
  - 🟡 **Legendary**
  - 💠 **Cosmic**, 💮 **Exclusive**, 🔮 **Limited Edition**, 🫧 **Royal** (Special Thresholds)
- 📊 **Advanced Economy**: Integrated collection system with user-specific statistics.
- 🛡️ **Robust Admin Tools**: Comprehensive command set for bot management and sudo users.
- 🐳 **Docker Ready**: Modular architecture optimized for containerized environments.
- 🚀 **Cloud-Native**: Native support for Heroku and other PaaS providers.

## 🛠️ Tech Stack

- **Language**: Python 3.12+
- **Framework**: [Pyrogram](https://github.com/pyrogram/pyrogram) (MTProto)
- **Database**: [MongoDB](https://www.mongodb.com/) (Motor)
- **APIs**: ImgBB (Image Hosting), Extol (Special APIs)
- **Environment**: Docker, Heroku

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- MongoDB Instance (Atlas recommended)
- Telegram `API_ID` and `API_HASH` (get from [my.telegram.org](https://my.telegram.org))
- Telegram `BOT_TOKEN` (get from [@BotFather](https://t.me/BotFather))

## 🐳 Deployment

### Docker

```bash
docker build -t seal-bot .
docker run seal-bot
```

### Heroku

This repository is optimized for Heroku via the included `Procfile` and `heroku.yml`.

- Set `PYTHON_VERSION` to `3.12`
- Add MongoDB addon or use external Atlas URI.
- Set `SUDO_USERS` and other environment variables.

## 📜 Commands

### 👤 General

- `/start` - Start the bot.
- `/ping` - Check bot and database latency.
- `/profile` - View your profile and statistics.
- `/help` - Show help menu (if available).

### 🦋 Collection

- `/seal <name>` - Catch a spawned character.
- `/harem` / `/collection` - View your caught characters.
- `/fav` / `/sfav` - Set or view your favorite character.
- `/check` - Check character details by ID.
- `/rarities` - View list of character rarities.
- `/search` - Search for a character in the global database.

### 💰 Economy & Shop

- `/balance` / `/bal` - Check your currency balance.
- `/daily` / `/bonus` - Claim daily rewards.
- `/pay` - Send currency to another user.
- `/shop` / `/cshop` - Open the character and item shop.
- `/sell` - Sell a character for currency.
- `/exchange` - Exchange different types of currency.
- `/mypet` / `/pets` - View your pets.
- `/petshop` - Buy pets.

### ⚔️ Battle & Progress

- `/battle` - Start a battle with other users.
- `/quests` - View daily and weekly quests.
- `/pass` / `/level` - View Battle Pass progress.
- `/hunt` / `/hatch` - Hunt for eggs and hatch them.

### 🛡️ Admin & Sudo

- `/broadcast` - Send a message to all users (Owner only).
- `/addsudo` / `/rmsudo` - Manage sudo users.
- `/givebalance` / `/takebalance` - Adjust user balance.
- `/upload` - Upload new characters to the database.
- `/changetime` - Change spawn frequency in a group.
- `/eval` / `/py` - Execute python code (Authorized users).
- `/mongobackup` - Create a database backup.

## ⚙️ Configuration

| Variable     | Description                      | Default  |
| ------------ | -------------------------------- | -------- |
| `TOKEN`      | Telegram Bot Token               | Required |
| `API_ID`     | Telegram API ID                  | Required |
| `MONGO_URL`  | MongoDB Connection URI           | Required |
| `OWNER_ID`   | Telegram ID of the bot owner     | Required |
| `SUDO_USERS` | Comma-separated list of sudo IDs | Optional |

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  Built with ❤️ by the Seal-Bot Team
</div>
