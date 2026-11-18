# IntelKit — AI-Powered Content Intelligence

**Current Status:** Stage 1 — Project Foundation

IntelKit is a Telegram bot built with Python, FastAPI, and `python-telegram-bot` that transforms Instagram content and uploaded media into concise, structured knowledge (**Signal, not noise**).

Stage 1 sets up the core backend server, Telegram bot initialization, webhook foundation, safe logging, environment configuration, and tests. AI processing, media pipelines, and cloud deployment come in later stages.

## Project Structure

```text
.
├── .env.example              # Template for environment variables (no real secrets)
├── .gitignore                # Prevents committing .env, virtualenvs, and cache files
├── README.md                 # Setup and testing guide
├── requirements.txt          # Python packages needed for Stage 1
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI server (/health and /webhook/telegram)
│   ├── config.py             # Loads and validates environment variables
│   ├── logging_config.py     # Safe logging that redacts API keys and tokens
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── client.py         # Initializes python-telegram-bot Application
│   │   └── handlers.py       # /start, /help, and basic text message handlers
│   └── utils/
│       ├── __init__.py
│       ├── deduplication.py  # Ignores duplicate Telegram update deliveries
│       └── text_router.py    # Classifies incoming text and Instagram URLs
├── scripts/
│   └── set_webhook.py        # Helper to register/check your Telegram webhook URL
└── tests/
    ├── __init__.py
    ├── test_core.py          # Unit tests for config, logging, deduplication, routing
    └── test_api.py           # Integration tests for FastAPI & webhook endpoints
```

## Local Setup (Step by Step)

1. **Create a Python virtual environment** (requires Python 3.11+):
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in `TELEGRAM_BOT_TOKEN` (from `@BotFather`) and an optional `TELEGRAM_WEBHOOK_SECRET` (any random string you invent).

4. **Run the automated tests:**
   ```bash
   pytest -v
   ```

5. **Start the FastAPI server locally:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Visit `http://localhost:8000/health` in your browser to confirm `{"status": "ok", ...}`.

6. **Connect Telegram locally using a public HTTPS tunnel (e.g., ngrok):**
   - Start ngrok in a second terminal:
     ```bash
     ngrok http 8000
     ```
   - Copy the `https://....ngrok-free.app` URL into `WEBHOOK_BASE_URL` in `.env`, then run:
     ```bash
     python scripts/set_webhook.py set
     ```
   - Message `/start`, `/help`, or any text to your bot on Telegram!
