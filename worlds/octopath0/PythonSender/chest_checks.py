"""Read-only chest snapshots, bound watches, and check-payload previews.

These helpers do not submit commands to Archipelago or grant game items.
"""

import json
import time
import uuid

from bridge_io import publish


# Verified prototype mapping shared by previews and live check submission.
PROTOTYPE_LOCATIONS = {
    ("treasure", 70117): {
        "name": "Cerulean Caverns - Southwest Cliff Chest",
        "ap_location_id": 10_000_001,
    },
}

def build_location_check_preview(source_kind, source_id, status, observation):
    if status != "complete" or observation != "checked":
        raise RuntimeError("Only a completed, checked watch can produce a payload.")

    location = PROTOTYPE_LOCATIONS.get((source_kind, source_id))
    if location is None:
        raise RuntimeError(
            f"No AP location mapping for {source_kind} {source_id}."
        )

    ap_id = location["ap_location_id"]
    if type(ap_id) is not int or not 0 < ap_id <= 2**53 - 1:
        raise RuntimeError("Invalid prototype AP location ID.")

    commands = [{"cmd": "LocationChecks", "locations": [ap_id]}]
    return location, commands


def run_checks_test(folder, timeout):
    request_id = uuid.uuid4().hex
    query = f"OT0AP_CHECKS_QUERY_V1\n{request_id}\n"

    publish(folder / "inbox.txt", query)

    # Do not change last_request.txt: --status reads delivery responses.
    print(f"\nPublished read-only checks query {request_id}", flush=True)
    print(
        "Disarm delivery with Ctrl+F3, then press Ctrl+F7 "
        "on the intended loaded save.",
        flush=True,
    )

    snapshot = folder / f"{request_id}.checks"
    failure = folder / f"{request_id}.checks-error"
    deadline = time.monotonic() + timeout

    while True:
        current_query = (folder / "inbox.txt").read_text(encoding="utf-8")
        if current_query != query:
            raise RuntimeError(
                "Inbox changed during checks inspection. Stopping."
            )

        try:
            with failure.open("rb") as handle:
                message = handle.read(4096).decode(
                    "utf-8", errors="replace"
                ).strip()
        except FileNotFoundError:
            pass
        else:
            raise RuntimeError(f"Checks inspection failed: {message}")

        try:
            with snapshot.open("rb") as handle:
                raw = handle.read(4097)
        except FileNotFoundError:
            raw = None

        if raw is not None:
            break

        if time.monotonic() >= deadline:
            raise RuntimeError(
                "Timed out waiting for the checks snapshot. "
                "Inspect the game log. This request does not authorize "
                "item delivery."
            )

        time.sleep(0.5)

    if len(raw) > 4096:
        raise RuntimeError("Checks snapshot exceeds the prototype size limit.")

    lines = raw.decode("utf-8").splitlines()

    if (
        len(lines) != 7
        or lines[0] != "OT0AP_CHECKS_V2"
        or lines[1] != request_id
        or lines[2] != "treasure"
        or lines[3] in {"", "unknown", "nil"}
        or lines[4] != "70117"
        or lines[5] not in {"checked", "not_detected", "unknown"}
        or lines[6] != "END"
    ):
        raise RuntimeError("Invalid or mismatched checks snapshot.")

    descriptions = {
        "checked": "Verified completion value observed.",
        "not_detected": (
            "Record exists; verified completion value was not observed."
        ),
        "unknown": "No matching treasure record was found.",
    }

    observation = lines[5]

    print(f"\nObserved save: {lines[3]}")
    print("Treasure 70117: Cerulean Caverns - Southwest Cliff Chest")
    print(f"Observation: {observation}")
    print(descriptions[observation])
    print(
        "Snapshot taken when Ctrl+F7 handled this query; "
        "not a live status or proof of a disk save."
    )
    print("No delivery metadata was required or changed.")
    print("No item delivery was authorized.")
    print("No location checks were sent to Archipelago.")

def run_checks_watch(folder, timeout, dry_run_locations=False):
    request_id = uuid.uuid4().hex
    query = f"OT0AP_WATCH_QUERY_V1\n{request_id}\n"

    publish(folder / "inbox.txt", query)

    print(f"\nPublished read-only watch {request_id}", flush=True)
    print(
        "Disarm with Ctrl+F3, then press Ctrl+F7 on the intended save. "
        "Ctrl+F3 also stops an active watch.",
        flush=True,
    )

    deadline = time.monotonic() + timeout
    sequence = 0
    bound_save = None

    while True:
        path = folder / f"{request_id}.watch.{sequence}"

        try:
            with path.open("rb") as handle:
                raw = handle.read(8193)
        except FileNotFoundError:
            raw = None

        if raw is not None:
            if len(raw) > 8192:
                raise RuntimeError("Watch event exceeds the size limit.")

            lines = raw.decode("utf-8").splitlines()

            if (
                len(lines) != 8
                or lines[0] != "OT0AP_WATCH_V1"
                or lines[1] != request_id
                or lines[3] != "70117"
                or lines[4] not in {
                    "watching", "complete", "stopped", "blocked", "error"
                }
                or lines[5] not in {
                    "checked", "not_detected", "unknown"
                }
                or lines[7] != "END"
            ):
                raise RuntimeError("Invalid watch event.")

            save_name = lines[2]
            status = lines[4]
            observation = lines[5]

            if status in {"watching", "complete"}:
                if save_name in {"", "unknown", "nil"}:
                    raise RuntimeError("Watch event lacks a save identity.")

                if status == "complete" and observation != "checked":
                    raise RuntimeError("Invalid watch completion.")

                if status == "watching" and observation == "checked":
                    raise RuntimeError("Invalid continuing-watch state.")

                if bound_save is None:
                    bound_save = save_name
                    print(f"Bound save: {bound_save}", flush=True)

            if bound_save is not None and save_name != bound_save:
                raise RuntimeError("Watch event changed its bound-save identity.")

            print(
                f"Treasure 70117: {observation}; watch={status}",
                flush=True,
            )
            print(lines[6], flush=True)
            sequence += 1

            if status == "complete":
                if dry_run_locations:
                    location, commands = build_location_check_preview(
                        "treasure", int(lines[3]), status, observation
                    )
                    print(
                        f"DRY RUN: {location['name']} -> "
                        f"AP location {location['ap_location_id']}",
                        flush=True,
                    )
                    print("Would send (provisional mapping; nothing sent):", flush=True)
                    print(json.dumps(commands), flush=True)

                print(
                    "Watch finished. Returning the verified in-memory observation.",
                    flush=True,
                )
                return {
                    "request_id": request_id,
                    "save": bound_save,
                    "treasure_id": int(lines[3]),
                    "status": status,
                    "observation": observation,
                }

            if status == "stopped":
                print("Read-only watch stopped.", flush=True)
                return

            if status in {"blocked", "error"}:
                raise RuntimeError(
                    "Read-only watch ended. Inspect the result before "
                    "authorizing a new watch."
                )

        if time.monotonic() >= deadline:
            raise RuntimeError(
                "Watch timed out. Press Ctrl+F3 in-game to stop any "
                "remaining watch. No item delivery was authorized."
            )

        time.sleep(0.5)
