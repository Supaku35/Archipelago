import argparse
import asyncio
import os
import uuid
from pathlib import Path

from save_binding import request_save_binding
from ap_connection import SEED, expect
from ap_history import read_verified_history, plan_pending
from bridge_io import BridgeCancelled, publish, wait_for_bridge_response

def main(argv=None, *, run_state=None):
    if run_state is None:
        run_state = {"delivery_attempted": False, "processed": False}
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--replay-index-zero", action="store_true")
    args = parser.parse_args(argv)
    if args.timeout < 1:
        raise RuntimeError("Timeout must be positive.")

    history = asyncio.run(read_verified_history())
    binding = request_save_binding("authorize")
    if binding is None:
        raise RuntimeError("No live binding. Initialize it separately first.")

    expect("Live seed", binding["seed"], SEED)
    expect("Live team", binding["team"], 0)
    expect("Live slot", binding["slot"], 1)
    pending = plan_pending(history, binding["next_index"])

    if args.replay_index_zero:
        expect("Duplicate-test starting progress", binding["next_index"], 1)
        print("DUPLICATE TEST: replaying index 0; no grant should occur.")
    elif not pending:
        print("Already caught up. No delivery request published.")
        print("Press Ctrl+F3 to clear this run's authorization.")
        return

    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise RuntimeError("LOCALAPPDATA is unavailable.")
    folder = Path(root) / "OctopathArchipelagoBridge"

    request_id = uuid.uuid4().hex
    item = history[0]
    payload = (
        f"OT0AP_LIVE_V1\n{request_id}\n{binding['token']}\n"
        f"{SEED}\n0\n1\n0\n{item['item']}\nEND\n"
    )
    # Mark before publication: an exception may occur after the inbox changed.
    run_state["delivery_attempted"] = True
    publish(folder / "inbox.txt", payload)

    print(f"Published live index 0; request {request_id}", flush=True)
    print(
        "Import and guarded application are automatic. "
        "Ctrl+F3 cancels a staged delivery.",
        flush=True,
    )

    next_index, _ = wait_for_bridge_response(
        folder, request_id, "processed", args.timeout,
        expected_save=binding["save_name"],
    )
    expect("Processed live progress", next_index, 1)
    run_state["processed"] = True

    print("Live index 0 accounted for in memory; authorization cleared.")
    print("Save normally to persist. No checks or goal submitted.")


def run_cli(argv=None):
    state = {"delivery_attempted": False, "processed": False}
    try:
        main(argv, run_state=state)
    except BridgeCancelled:
        print("Live delivery cancelled: the bridge discarded this staged request.")
        print("No grant or progress change for the cancelled request. No automatic retry.")
        return 1
    except KeyboardInterrupt:
        print("Stopped by user.")
        print_delivery_stop_guidance(state)
        return 0
    except Exception as exc:
        print(f"Live delivery stopped: {type(exc).__name__}: {exc}")
        print_delivery_stop_guidance(state)
        return 1
    return 0


def print_delivery_stop_guidance(state):
    if state["processed"]:
        print("A processed response was verified: live progress is 1 in memory.")
        print("Inspect the result before retrying; normal saving persists it.")
    elif state["delivery_attempted"]:
        print(
            "Delivery outcome is not confirmed. Press Ctrl+F3 in-game; "
            "a request may still be pending or may already have been applied."
        )
        print("Inspect before retrying. No automatic retry.")
    else:
        print("This run did not attempt to publish a live delivery request.")
        print("Press Ctrl+F3 to clear any remaining bridge authorization.")


if __name__ == "__main__":
    raise SystemExit(run_cli())
