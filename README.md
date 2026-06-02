# Seal-Bot

A high-performance, modular Telegram bot ecosystem combining interactive chat functionality with a premium React-based WebApp. Built on a Unified Web Service architecture, it leverages a single process for both the bot and API, ensuring shared memory usage and low-latency asynchronous execution.

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-Cloud-red?logo=redis&logoColor=white)](https://redis.io/)

---

## Overview

Seal-Bot integrates a Pyrogram-based (Kurigram) interactive chat bot with a modern Vite + React 19 Telegram WebApp (TWA).

The architecture introduces a **Unified Web Service** model: a FastAPI application hosts the REST endpoints, while a Lifespan context manager gracefully handles the startup and teardown of the Telegram bot within the same process. This allows direct, low-latency access to the underlying asynchronous data layers (MongoDB + Redis).

## Project Architecture

```text
Seal-Bot-V2/
├── Grabber/                # Main Application Package
│   ├── core/               # Core Systems (Cache, Sessions)
│   ├── database/           # MongoDB Connection & Models
│   ├── modules/            # Bot Feature Modules
│   └── webapp/             # FastAPI App & REST Endpoints
├── frontend/               # Vite/React TWA Static Assets
├── config.py               # Global Configuration
├── pyproject.toml          # Modern Python Dependencies
└── Dockerfile              # Containerization
```

## Features

- **Unified Process:** Fast, shared-memory execution using ASGI (Uvicorn).
- **Premium Frontend:** React 19 and Tailwind CSS v4, optimized with Vite 8.
- **Robust Caching:** Redis implementation for session state and high-frequency read operations, falling back safely to MongoDB.
- **Secure Sessions:** HMAC-SHA256 validation of Telegram `initData` ensures secure access to the REST API.
- **Scalable Database:** Document-oriented models designed for MongoDB Atlas.

## Tech Stack & Tooling

### Backend
- **Python >= 3.14**
- **FastAPI** for high-performance REST APIs.
- **PyMongo AsyncMongoClient** for asynchronous MongoDB operations.
- **Redis (Upstash/Native)** for fast caching.
- **Kurigram / Pyrogram** for Telegram Bot operations.

### Frontend
- **Node >= 22**
- **React 19 & Vite 8**
- **Tailwind CSS v4**
- **Stable TypeScript (`tsc`) with TypeScript ESLint**

## Setup & Local Development

### 1. Environment Configuration

Copy the sample environment file and fill in your credentials.

`cp sample.env .env`

Required variables:
- `TOKEN`, `API_ID`, `API_HASH`
- `MONGO_URL`, `REDIS_URL`
- `WEB_APP_URL`

### 2. Frontend Development

Ensure you have Node.js 22 installed (using `nvm` or equivalent).

`cd frontend`
`npm install`
`npm run build`

### 3. Backend Development

Ensure Python 3.14+ is installed.

`uv sync`
`uv run python -m Grabber`

## Logging

Logging is configured centrally at package startup. By default the service writes redacted text logs to stdout, which is the safest mode for Linux containers and PaaS deployments. Rotating file logs can be enabled explicitly with `LOG_FILE_ENABLED=true`.

Useful environment variables:
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `LOG_FORMAT`: `text` or `json`.
- `LOG_FILE_ENABLED`: set to `true` to also write rotating file logs.
- `LOG_DIR`, `LOG_FILE`, `LOG_MAX_BYTES`, `LOG_BACKUP_COUNT`: rotating file log controls.
- `LOG_UTC`: set to `true` for UTC timestamps.

Sensitive values such as bot tokens, MongoDB/Redis credentials, API keys, and session strings are redacted before log output. Web API responses include `X-Request-ID`, and request logs include the same ID for correlation.

## Resource Management

The service starts a lightweight resource monitor with the bot lifecycle and manages limits automatically by default. It detects Linux cgroup memory limits when available, falls back to process/host memory limits, tracks process RSS memory, available system memory, open descriptor count where supported, and active background-task count. Under memory pressure it runs garbage collection and purges bounded batches of volatile Redis cache keys (`user:*`, `balance:*`, leaderboard/rank caches) without deleting active spawn state or durable counters.

Useful environment variables:
- `RESOURCE_MONITOR_ENABLED`: enable or disable the monitor.
- `RESOURCE_MEMORY_SOFT_LIMIT_MB` / `RESOURCE_MEMORY_HARD_LIMIT_MB`: optional process RSS threshold overrides. `0` lets the bot auto-detect.
- `RESOURCE_MIN_AVAILABLE_MB`: optional low-memory override. `0` lets the bot derive a safe value automatically.
- `RESOURCE_TASK_SOFT_LIMIT`: warn when tracked background tasks grow unexpectedly.
- `RESOURCE_REDIS_PURGE_BATCH_SIZE` and `REDIS_MEMORY_LIMIT_MB`: optional Redis cleanup controls. `REDIS_MEMORY_LIMIT_MB=0` lets the bot use Redis `maxmemory` when available, otherwise a conservative internal cache budget.

## Deployment

The service can be containerized and deployed natively using Docker. The multi-stage `Dockerfile` is optimized to build dependencies (wheels) in an isolated stage and execute as a non-root user (`botuser`) in the final image.

### Docker (Standard)

`docker build -t seal-bot .`
`docker run --env-file .env seal-bot`

### Platform-as-a-Service (PaaS)
- **Heroku:** Uses `heroku.yml` or standard container stack.
- **Render / Koyeb:** Configure Docker as the build environment and supply `.env` variables via their respective UI consoles.

## WebApp Registration

To ensure native behavior in the Telegram client, the WebApp must be registered via [@BotFather](https://t.me/BotFather):
1. Navigate to **Bot Settings** > **Mini App**.
2. Enable the Mini App and provide the deployment `WEB_APP_URL`.
3. Set your preferred short name (update `MINI_APP_SHORT_NAME` in config if changed from `app`).

## Security

API routes are protected via Bearer token authorization. When the WebApp is initialized, Telegram's payload is cryptographically verified on the `/secure_init` endpoint. Validated sessions are assigned a secure UUID and cached in Redis.

## License

This project is licensed under the terms specified in the `LICENSE` file.
