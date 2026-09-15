"""Application configuration and environment variable loading.

This module loads environment variables from a ``.env`` file (if present) and
validates that all required variables are present before the application starts.
Missing or empty values raise a clear :class:`ValueError` so misconfiguration is
caught early rather than failing deep inside the application.
"""

import os
from typing import Dict, List

from dotenv import load_dotenv

# Load variables from a local .env file into the process environment.
load_dotenv()

# Centralised list of required environment variables.
REQUIRED_VARS: List[str] = [
    "TELEGRAM_TOKEN",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "KIOSAPI_KEY",
]


def _validate_required_vars() -> Dict[str, str]:
    """Validate that every required environment variable is set.

    Returns:
        A mapping of variable name to its non-empty string value.

    Raises:
        ValueError: If any required variable is missing or empty.
    """
    missing: List[str] = []
    values: Dict[str, str] = {}

    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            values[var] = value

    if missing:
        raise ValueError(
            "Missing required environment variable(s): "
            f"{', '.join(missing)}. "
            "Please check your .env file (see .env.example for the expected keys)."
        )

    return values


# Validate and export configuration values at import time.
_CONFIG: Dict[str, str] = _validate_required_vars()

TELEGRAM_TOKEN: str = _CONFIG["TELEGRAM_TOKEN"]
SUPABASE_URL: str = _CONFIG["SUPABASE_URL"]
SUPABASE_KEY: str = _CONFIG["SUPABASE_KEY"]
KIOSAPI_KEY: str = _CONFIG["KIOSAPI_KEY"]
