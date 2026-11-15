"""Command-line entry point for read-only AP connection inspection."""

import asyncio

# Re-export the existing names for callers of older prototype scripts.
from ap_connection import (
    EXPECTED_SLOT_DATA, GAME, LOCATION, PLAYER, SEED, SERVER,
    expect, inspect_connection, receive_command,
)


if __name__ == "__main__":
    try:
        asyncio.run(inspect_connection())
    except KeyboardInterrupt:
        print("Inspection cancelled.")
    except TimeoutError:
        raise SystemExit("Inspection timed out; connection closed. No automatic retry.")
    except Exception as exc:
        raise SystemExit(f"Inspection failed: {exc}")
