"""Personal Assistant Telegram Bot - Phase 1.

This is the entry point for the bot. It wires up command and message handlers,
persists every user/bot exchange to Supabase via :mod:`database`, and provides a
``/memory`` command that renders the user's saved topic memories.

Run locally with::

    python bot.py

Or deploy on Railway where the ``Procfile`` launches this module as a worker.
"""

import logging
from typing import Any, Dict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import database

# Configure root logging for the application.
# DEBUG gives visibility into incoming updates; we quiet the HTTP client noise.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

WELCOME_MESSAGE = (
    "👋 *Welcome to your Personal Assistant!*\n\n"
    "I'm here to help you stay organised. Right now I can:\n"
    "• 💬 Echo your messages back to confirm I heard you\n"
    "• 🧠 Remember things for you, organised by topic\n\n"
    "Use /memory to see what I've remembered, and /help for this message again."
)


class PersonalAssistant:
    """Encapsulates the Telegram bot application and its handlers."""

    def __init__(self) -> None:
        """Build the Application and register all handlers."""
        self.application = (
            Application.builder().token(config.TELEGRAM_TOKEN).build()
        )
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Attach command and message handlers to the application."""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("memory", self.memory_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        # Debug: log every incoming message. Runs in its own handler group so it
        # never blocks the real handlers above.
        self.application.add_handler(
            MessageHandler(filters.ALL, self._log_update), group=99
        )
        # Surface any exception raised while handling an update.
        self.application.add_error_handler(self.error_handler)

    async def _log_update(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Debug-only handler that logs every incoming message update."""
        user = update.effective_user
        text = update.message.text if update.message else None
        logger.debug(
            "Incoming update_id=%s from user=%s (@%s): %r",
            update.update_id,
            getattr(user, "id", None),
            getattr(user, "username", None),
            text,
        )

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log any exception raised while handling an update."""
        logger.error("Exception while handling update %s:", update, exc_info=context.error)

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Send the welcome message (also used by /help)."""
        try:
            user = update.effective_user
            logger.info("Command /start from user %s (@%s)", user.id, user.username)
            await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")
        except Exception:
            logger.exception("Failed to send start/help message")

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Alias for the start command."""
        await self.start_command(update, context)

    async def memory_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Display all saved memories grouped by topic with emojis."""
        user_id = update.effective_user.id
        try:
            memories: Dict[str, Dict[str, str]] = await database.get_all_memories(
                user_id
            )
            if not memories:
                await update.message.reply_text(
                    "🧠 I don't have any memories saved for you yet. "
                    "I'll start remembering things soon!"
                )
                return

            lines = ["🧠 *Your Saved Memories*\n"]
            for topic, items in memories.items():
                lines.append(f"📁 *{topic}*")
                if not items:
                    lines.append("  _(no entries)_")
                for key, value in items.items():
                    lines.append(f"  • *{key}*: {value}")
                lines.append("")  # blank line between topics

            await update.message.reply_text(
                "\n".join(lines).strip(), parse_mode="Markdown"
            )
        except Exception:
            logger.exception("Failed to render memory command for user %s", user_id)
            await update.message.reply_text(
                "⚠️ Sorry, I couldn't retrieve your memories right now."
            )

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Echo the user's message, persisting both sides of the exchange."""
        user = update.effective_user
        user_id = user.id
        text = update.message.text
        logger.info("Message from %s (@%s): %r", user_id, user.username, text)

        try:
            # Persist the incoming user message.
            await database.save_message(user_id, text, "user")

            # Simple echo response for Phase 1.
            response = f"🤖 Echo: {text}"
            await update.message.reply_text(response)

            # Persist the bot's response.
            await database.save_message(user_id, response, "assistant")
        except Exception:
            logger.exception("Error handling message from user %s", user_id)
            await update.message.reply_text(
                "⚠️ Sorry, something went wrong while processing your message."
            )

    def run(self) -> None:
        """Start the bot using long-polling."""
        logger.info("Starting Personal Assistant bot...")
        self.application.run_polling()


def main() -> None:
    """Application entry point."""
    assistant = PersonalAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
