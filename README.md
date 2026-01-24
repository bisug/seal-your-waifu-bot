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

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TOKEN` | Telegram Bot Token | Required |
| `API_ID` | Telegram API ID | Required |
| `MONGO_URL` | MongoDB Connection URI | Required |
| `OWNER_ID` | Telegram ID of the bot owner | Required |
| `SUDO_USERS` | Comma-separated list of sudo IDs | Optional |

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---
<div align="center">
  Built with ❤️ by the Seal-Bot Team
</div>
