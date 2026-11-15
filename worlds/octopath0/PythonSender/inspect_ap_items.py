"""Command-line entry point for read-only AP item-history inspection."""

import asyncio

from ap_connection import inspect_connection
# Keep the previous helper names available to older callers.
from ap_history import FIELDS, EXPECTED_ITEM, validate_history, inspect_history


if __name__ == "__main__":
    try:
        asyncio.run(inspect_connection(after_verified=inspect_history))
        print("PASS: item history inspected; no items granted or checks submitted.")
    except KeyboardInterrupt:
        print("Item inspection cancelled.")
    except TimeoutError:
        raise SystemExit("Item inspection timed out. No automatic retry.")
    except Exception as exc:
        raise SystemExit(f"Item inspection failed: {type(exc).__name__}: {exc}")
