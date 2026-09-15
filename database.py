"""Async database access layer backed by Supabase (PostgreSQL).

The ``supabase`` Python SDK is synchronous, so each blocking call is wrapped in
:func:`asyncio.to_thread` to keep the bot's event loop responsive.

All public functions guarantee they will not raise: on error they log the
exception and return an empty container (``[]`` or ``{}``) so callers can
continue operating safely.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

import config

logger = logging.getLogger(__name__)

# Module-level Supabase client initialised from validated configuration.
_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

# Default topic used when none is supplied by the caller.
DEFAULT_TOPIC: str = "general"


async def save_message(
    user_id: int,
    message: str,
    role: str,
    topic: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Save a single conversation message to the ``conversations`` table.

    Args:
        user_id: Telegram user identifier.
        message: The message text.
        role: Either ``"user"`` or ``"assistant"`` (or any role label).
        topic: Optional topic label. Falls back to ``DEFAULT_TOPIC``.

    Returns:
        The inserted row as a dictionary, or ``None`` on failure.
    """
    payload = {
        "user_id": user_id,
        "message": message,
        "role": role,
        "topic": topic or DEFAULT_TOPIC,
    }
    try:
        result = await asyncio.to_thread(
            lambda: _client.table("conversations").insert(payload).execute()
        )
        rows = getattr(result, "data", None)
        if rows:
            logger.debug("Saved %s message for user %s", role, user_id)
            return rows[0]
        logger.warning("No data returned when saving message for user %s", user_id)
        return None
    except Exception:
        logger.exception("Failed to save message for user %s", user_id)
        return None


async def get_recent_messages(
    user_id: int,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Return the most recent conversation messages for a user.

    The rows are returned in **chronological** (oldest-first) order regardless
    of how they are stored, which is convenient for building a chat context.

    Args:
        user_id: Telegram user identifier.
        limit: Maximum number of messages to return.

    Returns:
        A list of message rows ordered oldest-first, or ``[]`` on failure.
    """
    try:
        result = await asyncio.to_thread(
            lambda: (
                _client.table("conversations")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        )
        rows = getattr(result, "data", []) or []
        # Reverse so the caller receives them in chronological order.
        return list(reversed(rows))
    except Exception:
        logger.exception("Failed to fetch recent messages for user %s", user_id)
        return []



async def save_memory(
    user_id: int,
    topic: str,
    key: str,
    value: str,
) -> Optional[Dict[str, Any]]:
    """Upsert a single key/value memory for a user within a topic.

    If a memory with the same ``(user_id, topic, key)`` already exists it is
    updated in place; otherwise a new row is inserted.

    Args:
        user_id: Telegram user identifier.
        topic: Topic label this memory belongs to.
        key: Memory key (unique within the topic for the user).
        value: Memory value (stored as text).

    Returns:
        The upserted row as a dictionary, or ``None`` on failure.
    """
    payload = {
        "user_id": user_id,
        "topic": topic,
        "key": key,
        "value": value,
    }
    try:
        result = await asyncio.to_thread(
            lambda: (
                _client.table("topic_memories")
                .upsert(payload, on_conflict="user_id,topic,key")
                .execute()
            )
        )
        rows = getattr(result, "data", None)
        if rows:
            logger.debug("Saved memory %s/%s for user %s", topic, key, user_id)
            return rows[0]
        logger.warning(
            "No data returned when saving memory %s/%s for user %s",
            topic,
            key,
            user_id,
        )
        return None
    except Exception:
        logger.exception(
            "Failed to save memory %s/%s for user %s", topic, key, user_id
        )
        return None


async def get_topic_memories(
    user_id: int,
    topic: str,
) -> Dict[str, str]:
    """Return all memories for a single topic as a flat key/value mapping.

    Args:
        user_id: Telegram user identifier.
        topic: Topic label to fetch memories for.

    Returns:
        A ``{key: value}`` dictionary, or ``{}`` on failure or no data.
    """
    try:
        result = await asyncio.to_thread(
            lambda: (
                _client.table("topic_memories")
                .select("key, value")
                .eq("user_id", user_id)
                .eq("topic", topic)
                .execute()
            )
        )
        rows = getattr(result, "data", []) or []
        return {row["key"]: row["value"] for row in rows}
    except Exception:
        logger.exception(
            "Failed to fetch memories for topic %s, user %s", topic, user_id
        )
        return {}


async def get_all_memories(
    user_id: int,
) -> Dict[str, Dict[str, str]]:
    """Return all memories for a user grouped by topic.

    Args:
        user_id: Telegram user identifier.

    Returns:
        A ``{topic: {key: value}}`` dictionary, or ``{}`` on failure or no data.
    """
    try:
        result = await asyncio.to_thread(
            lambda: (
                _client.table("topic_memories")
                .select("topic, key, value")
                .eq("user_id", user_id)
                .execute()
            )
        )
        rows = getattr(result, "data", []) or []
        grouped: Dict[str, Dict[str, str]] = {}
        for row in rows:
            topic = row["topic"]
            grouped.setdefault(topic, {})[row["key"]] = row["value"]
        return grouped
    except Exception:
        logger.exception("Failed to fetch all memories for user %s", user_id)
        return {}

