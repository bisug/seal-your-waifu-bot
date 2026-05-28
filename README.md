# Seal-Bot

A high-performance, modular Telegram bot ecosystem combining interactive chat functionality with a premium React-based WebApp. Built on a Unified Web Service architecture, it leverages a single process for both the bot and API, ensuring shared memory usage and low-latency asynchronous execution.

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
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
- **Premium Frontend:** React 19 and Tailwind CSS v4, optimized with Vite 6.
- **Robust Caching:** Redis implementation for session state and high-frequency read operations, falling back safely to MongoDB.
- **Secure Sessions:** HMAC-SHA256 validation of Telegram `initData` ensures secure access to the REST API.
- **Scalable Database:** Document-oriented models designed for MongoDB Atlas.

## Tech Stack & Tooling

### Backend
- **Python >= 3.14**
- **FastAPI** for high-performance REST APIs.
- **Motor (PyMongo)** for asynchronous MongoDB operations.
- **Redis (Upstash/Native)** for fast caching.
- **Kurigram / Pyrogram** for Telegram Bot operations.

### Frontend
- **Node >= 22**
- **React 19 & Vite 6**
- **Tailwind CSS v4**
- **TypeScript (`tsgo` via `@typescript/native-preview`)**

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

`pip install -e .`
`python3 -m Grabber`

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
