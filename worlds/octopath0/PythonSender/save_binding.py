import asyncio
import os
import re
import time
import uuid
from pathlib import Path

from ap_connection import SEED, expect, inspect_connection
from bridge_io import publish
from two_chest_profiles import REVISED_SEED, verify_revised_room


def request_save_binding(operation, *, test_mismatch=False, revised=False):
    if operation not in {"initialize", "inspect", "authorize"}:
        raise ValueError("Unknown binding operation.")
    if test_mismatch and operation != "inspect":
        raise ValueError("Mismatch testing must be read-only.")

    initialize = operation == "initialize"
    inspect = operation == "inspect"
    authorize = operation == "authorize"

    # This verifier requires the known seed, team 0, slot 1, and mappings.
    seed = REVISED_SEED if revised else SEED
    asyncio.run(verify_revised_room() if revised else inspect_connection())

    if not re.fullmatch(r"[0-9]{1,64}", seed):
        raise RuntimeError("This metadata prototype supports numeric seed names only.")

    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise RuntimeError("LOCALAPPDATA is unavailable.")
    folder = Path(root) / "OctopathArchipelagoBridge"
    folder.mkdir(parents=True, exist_ok=True)

    request_id = uuid.uuid4().hex

    requested_slot = 2 if test_mismatch else 1
    payload = (
        f"OT0AP_BIND_V1\n{request_id}\n{operation}\n"
        f"{seed}\n0\n{requested_slot}\nEND\n"
    )
    publish(folder / "inbox.txt", payload)

    print(f"\nPublished live-binding request {request_id}", flush=True)
    if test_mismatch:
        print("READ-ONLY TEST: deliberately comparing against wrong slot 2.", flush=True)
    instructions = {
        "initialize": "Initialization requires exploration; this query grants no items.",
        "inspect": "Read-only inspection; no item delivery is authorized.",
        "authorize": "This authorizes live delivery for this run; the query grants nothing.",
    }
    print(
        "Select the intended save. Press Ctrl+F3 to disarm, then Ctrl+F7. "
        + instructions[operation],
        flush=True,
    )

    deadline = time.monotonic() + 180
    path = folder / f"{request_id}.binding"
    while True:
        if (folder / "inbox.txt").read_text(encoding="utf-8") != payload:
            raise RuntimeError("Inbox replaced. No automatic retry.")
        try:
            with path.open("rb") as handle:
                raw = handle.read(8193)
        except FileNotFoundError:
            raw = None

        if raw is not None:
            break
        if time.monotonic() >= deadline:
            timeout_detail = {
                "initialize": "Initialization may have occurred; do not assume it failed.",
                "inspect": "This was a read-only query; no delivery was authorized by it.",
                "authorize": "Authorization may remain active; press Ctrl+F3 to disarm.",
            }
            raise RuntimeError(
                "Binding response timed out. " + timeout_detail[operation] +
                " Do not press Ctrl+F7 for this old request; inspect with a new command."
            )
        time.sleep(0.5)

    if len(raw) > 8192:
        raise RuntimeError("Oversized binding response.")
    lines = raw.decode("utf-8").splitlines()
    if (
        len(lines) != 10
        or lines[0] != "OT0AP_BIND_RESPONSE_V1"
        or lines[1] != request_id
        or lines[2] not in {
            "initialized", "matched", "absent", "mismatch", "blocked", "not_ready",
            "authorized"
        }
        or lines[9] != "END"
    ):
        raise RuntimeError("Invalid binding response.")

    status = lines[2]
    print(f"Binding status: {status}")
    print(f"Observed save: {lines[3]}")
    print(lines[8])

    if status in {"blocked", "not_ready"}:
        raise RuntimeError("No automatic retry. Inspect the game log and result.")

    if lines[3] in {"", "unknown", "nil"}:
        raise RuntimeError("Missing save identity.")

    if status == "absent":
        if not inspect:
            raise RuntimeError("No initialized binding exists for this test.")
        expect("Absent metadata fields", lines[4:8], ["unknown"] * 4)
        return

    expect("Stored seed", lines[4], seed)
    expect("Stored team", lines[5], "0")
    expect("Stored slot", lines[6], "1")
    if not re.fullmatch(r"[0-9]{1,7}", lines[7]):
        raise RuntimeError("Invalid live-AP progress.")
    next_index = int(lines[7])
    if next_index > 1_000_000:
        raise RuntimeError("Live-AP progress exceeds the prototype limit.")

    if test_mismatch:
        expect("Intentional mismatch result", status, "mismatch")
        print("PASS: wrong slot rejected; original binding retained.")
    elif status == "mismatch":
        raise RuntimeError("Stored identity mismatch. Nothing reset.")
    elif status == "initialized":
        if not initialize:
            raise RuntimeError("Read-only request unexpectedly initialized metadata.")
        expect("Initial live-AP progress", next_index, 0)
    else:
        expect(
            "Binding result", status,
            "authorized" if authorize else "matched",
        )

    print(f"Live AP next delivery index: {next_index}")
    if status == "initialized":
        print("Binding initialized in memory; no items granted.")
        print("Save normally, then reload and inspect to verify disk persistence.")
    elif status == "authorized":
        print("Authorization only; this query granted no items or changed save metadata.")
    else:
        print("Existing metadata inspected; nothing initialized, reset, or granted.")
        print("This is an in-memory observation, not proof of a disk save.")

    return {
        "seed": lines[4],
        "team": int(lines[5]),
        "slot": int(lines[6]),
        "next_index": next_index,
        "token": request_id,
        "save_name": lines[3],
    }

