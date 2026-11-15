import argparse
import os
import re
import uuid
from pathlib import Path
from bridge_io import publish, read_response, wait_for_bridge_response
# Preserve the old helper imports while moving their implementation.
from chest_checks import (
    PROTOTYPE_LOCATIONS, build_location_check_preview,
    run_checks_test, run_checks_watch,
)


def run_coordinator_test(folder, timeout):
    stream_id = 101

    # Complete, fixed test history: indexes 0 through 8.
    # Preserve earlier entries when appending future deliveries.
    history = [(110001, 1) for _ in range(9)]

    request_id = uuid.uuid4().hex
    query = f"OT0AP_QUERY_V1\n{request_id}\n{stream_id}\n"

    publish(folder / "inbox.txt", query)
    publish(folder / "last_request.txt", request_id + "\n")

    print(f"\nPublished progress query {request_id}", flush=True)
    print(
        "On the intended loaded save, press Ctrl+F7 only. "
        "Do not change saves during this coordinator run.",
        flush=True,
    )

    next_index, bound_save = wait_for_bridge_response(
        folder, request_id, "progress", timeout
    )

    # The matching progress response confirms this query established a binding.
    binding_token = request_id

    if next_index > len(history):
        raise RuntimeError(
            "Save progress exceeds this sender's known history. "
            "Stopping without resetting anything."
        )

    print(
        f"Loaded save needs index {next_index}; "
        f"history contains {len(history)} deliveries.",
        flush=True,
    )

    if next_index == len(history):
        print("Already caught up. No item batches published.", flush=True)
        return

    while next_index < len(history):
        start_index = next_index
        item_id, quantity = history[start_index]
        request_id = uuid.uuid4().hex

        payload = (
            "OT0AP_TEST_V3\n"
            f"{request_id}\n"
            f"{stream_id}\n"
            f"{binding_token}\n"
            f"{start_index}\n"
            f"{item_id} {quantity}\n"
        )

        publish(folder / "inbox.txt", payload)
        publish(folder / "last_request.txt", request_id + "\n")

        print(
            f"\nPublished delivery {start_index}; request {request_id}",
            flush=True,
        )
        print(
            "Delivery imports automatically under the authorized save binding. "
            "Application waits for fresh gameplay checks to pass.",
            flush=True,
        )

        observed_next, _ = wait_for_bridge_response(
            folder, request_id, "processed", timeout,
            expected_save=bound_save,
        )

        if not start_index + 1 <= observed_next <= len(history):
            raise RuntimeError(
                "Processed counter is inconsistent with the known history."
            )

        next_index = observed_next

    print(
        "\nLoaded save caught up in memory. "
        "Save normally to persist the result.",
        flush=True,
    )

def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--status", action="store_true")
    modes.add_argument("--run-test", action="store_true")
    modes.add_argument("--checks", action="store_true")
    modes.add_argument("--watch-checks", action="store_true")

    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Maximum seconds to wait for each coordinated request.",
    )
    parser.add_argument(
        "--dry-run-locations",
        action="store_true",
        help="With --watch-checks, print a provisional AP check payload only.",
    )
    args = parser.parse_args()

    if args.dry_run_locations and not args.watch_checks:
        parser.error("--dry-run-locations requires --watch-checks.")

    if not (
        args.status or args.run_test or args.checks or args.watch_checks
    ):
        parser.error(
            "Use --run-test, --checks, --watch-checks, or --status."
        )

    if args.timeout < 1:
        parser.error("--timeout must be at least 1 second.")

    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise RuntimeError("LOCALAPPDATA is unavailable.")

    folder = Path(root) / "OctopathArchipelagoBridge"
    folder.mkdir(parents=True, exist_ok=True)
    latest = folder / "last_request.txt"

    if args.watch_checks:
        run_checks_watch(
            folder, args.timeout, dry_run_locations=args.dry_run_locations
        )
        return

    if args.checks:
        run_checks_test(folder, args.timeout)
        return

    if args.run_test:
        run_coordinator_test(folder, args.timeout)
        return

    if args.status:
        if not latest.exists():
            print("No request published by this sender yet.")
            return

        request_id = latest.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"[0-9a-f]{32}", request_id):
            raise RuntimeError("Invalid last-request ID.")

        response = folder / f"{request_id}.response"

        try:
            lines = response.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            print("No response currently available. Import the batch or retry status.")
            return

        if (
            len(lines) != 7
            or lines[0] != "OT0AP_RESPONSE_V1"
            or lines[1] != request_id
            or lines[6] != "END"
            or lines[2] not in {
            "staged", "deferred", "processed", "gap", "blocked", "progress",
            "cancelled"
            }
        ):
            raise RuntimeError("Response is incomplete or invalid.")

        print(f"Request: {request_id}")
        print(f"Status: {lines[2]}")
        print(f"Observed next index: {lines[3]}")
        print(f"Observed save object: {lines[4]}")
        print(f"Detail: {lines[5]}")
        print("Historical in-memory observation; not proof of a disk save.")
        return


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"Bridge error: {exc}")
