# GymTracker Backend

FastAPI backend for workout programs and history, with an optional Telegram bot.

## Backend setup

1. Create and activate a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set `DATABASE_URL` to your PostgreSQL connection string. Keep the provider's required SSL settings.
4. Run `uvicorn main:app --reload` for local development.

The backend creates missing tables when imported. Use a disposable database for tests. Never point local smoke tests at production data.

`BOT_TOKEN` is only needed by `bot.py`; the backend does not require it. The optional bot additionally uses `aiogram` and `aiosqlite` and has its own SQLite database.

## Credentials

Keep credentials in environment variables or an untracked local `.env`. `.env.example` intentionally contains no working credentials. Do not commit local databases or Python bytecode.

Previously committed credentials must be considered compromised. Removing them from the current files does not revoke them or remove them from Git history. Revoke the old Telegram bot token through BotFather and reset the exposed database role password in Neon before using those services again. Update any deployments with replacement credentials securely. History cleanup is a separate coordinated operation; old clones and cached copies may still exist.
