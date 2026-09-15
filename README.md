# Personal Assistant Telegram Bot

A Telegram bot with a topic-based memory system, built on
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot),
[Supabase](https://supabase.com/) (PostgreSQL), and deployable to
[Railway](https://railway.app/).

## What this bot does (Phase 1)

This is the **Phase 1 / core** release. The bot currently:

- 💬 Replies to the `/start` and `/help` commands with a welcome message.
- 🤖 Echoes any text message back to the user (simple echo behaviour).
- 💾 Persists **every** message exchange (user message + bot response) to the
  Supabase `conversations` table.
- 🧠 Provides a `/memory` command that displays all saved memories grouped by
  topic with emojis.
- 🗂️ Supports a topic-based memory system backed by the `topic_memories` table
  (upsert / read functions are implemented and ready for later phases).

Future phases will replace the echo handler with real NLP and richer memory
management.

## Project structure

```
personal-assistant-bot/
├── bot.py            # Main bot: handlers + PersonalAssistant class
├── config.py         # Loads & validates environment variables
├── database.py       # Async Supabase data access layer
├── requirements.txt  # Python dependencies
├── .env.example      # Template for required environment variables
├── .gitignore        # Files excluded from version control
├── Procfile          # Railway worker process
├── runtime.txt       # Python version for Railway
└── README.md         # This file
```

## Database schema

Tables are expected to already exist in Supabase:

- `conversations` (`id`, `user_id`, `message`, `role`, `topic`, `created_at`)
- `topic_memories` (`id`, `user_id`, `topic`, `key`, `value`, `created_at`,
  `updated_at`)

> The `topic_memories` table should have a unique constraint on
> `(user_id, topic, key)` so that `save_memory` can upsert correctly.

## Environment variables

Copy `.env.example` to `.env` and fill in the values:

| Variable         | Description                                        |
| ---------------- | -------------------------------------------------- |
| `TELEGRAM_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `SUPABASE_URL`   | Your Supabase project URL (e.g. `https://xxx.supabase.co`) |
| `SUPABASE_KEY`   | Supabase anon / public API key                     |
| `KIOSAPI_KEY`    | Key for the KiosAPI integration (used in later phases) |

The app **fails fast with a clear error** if any required variable is missing.

## Local setup

1. **Prerequisites**: Python 3.11+ and a Supabase project with the tables above.

2. **Clone / open** this folder:

   ```bash
   cd personal-assistant-bot
   ```

3. **Create a virtual environment** and install dependencies:

   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # macOS / Linux

   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   ```bash
   cp .env.example .env
   # then edit .env with your real values
   ```

5. **Run the bot**:

   ```bash
   python bot.py
   ```

   You should see a log line `Starting Personal Assistant bot...` and the bot
   will begin polling Telegram for updates.

## Deploying to Railway

1. Push this repository to GitHub (or connect your folder directly).

2. In Railway, create a **new project** → **Deploy from GitHub repo** (or use
   the Railway CLI).

3. Railway automatically picks up:
   - `runtime.txt` → pins **Python 3.11.0**
   - `Procfile` → runs `worker: python bot.py`

4. Add the **environment variables** (`TELEGRAM_TOKEN`, `SUPABASE_URL`,
   `SUPABASE_KEY`, `KIOSAPI_KEY`) in the Railway project's *Variables* tab.

5. Deploy. Railway starts the bot as a long-running worker process.

## Notes & limitations

- Phase 1 uses a simple echo handler; no natural language understanding yet.
- Database calls are wrapped in `asyncio.to_thread` because the Supabase SDK is
  synchronous, keeping the bot's event loop responsive.
- All database functions are defensive: on error they log the issue and return
  an empty `list` / `dict` (or `None`) instead of crashing the bot.
