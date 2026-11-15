import asyncio
import json
import os
from pathlib import Path

from ap_connection import expect, inspect_connection, receive_command
from chest_checks import build_location_check_preview, run_checks_watch


LOCATION_ID = 10000001
submission_attempted = False


async def submit_and_confirm(ws, checked):
    global submission_attempted

    if LOCATION_ID in checked:
        print("Server already has this check. Nothing submitted.")
        return

    payload = [{"cmd": "LocationChecks", "locations": [LOCATION_ID]}]
    submission_attempted = True
    await ws.send(json.dumps(payload))
    print("SUBMITTED: location 10000001; waiting for server confirmation.", flush=True)

    async with asyncio.timeout(20):
        while True:
            update = await receive_command(ws, "RoomUpdate")
            if "checked_locations" not in update:
                continue

            observed = update["checked_locations"]
            if not isinstance(observed, list) or any(
                type(value) is not int for value in observed
            ):
                raise RuntimeError("Invalid checked_locations confirmation.")
            if not set(observed).issubset({LOCATION_ID}):
                raise RuntimeError("Unexpected location in server confirmation.")

            if LOCATION_ID in observed:
                print("CONFIRMED: server reports location 10000001 checked.", flush=True)
                return


def main():
    checked = asyncio.run(inspect_connection())
    if LOCATION_ID in checked:
        print("Already checked on server. No watch started; nothing submitted.")
        return

    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise RuntimeError("LOCALAPPDATA is unavailable.")

    folder = Path(root) / "OctopathArchipelagoBridge"
    folder.mkdir(parents=True, exist_ok=True)

    print(
        "\nSelect the intended test save. Ctrl+F3 disarms; "
        "Ctrl+F7 authorizes the watch. A checked result WILL be submitted.",
        flush=True,
    )
    evidence = run_checks_watch(folder, 600)
    if evidence is None:
        print("Watch cancelled. No check submitted.")
        return

    _, commands = build_location_check_preview(
        "treasure", evidence["treasure_id"],
        evidence["status"], evidence["observation"],
    )
    expect(
        "Verified outgoing check", commands,
        [{"cmd": "LocationChecks", "locations": [LOCATION_ID]}],
    )
    print(
        f"Verified chest observation: save={evidence['save']} "
        f"watch={evidence['request_id']}",
        flush=True,
    )

    # Reconnect and revalidate the seed, slot, and mappings after watching.
    asyncio.run(inspect_connection(after_verified=submit_and_confirm))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped. Press Ctrl+F3 if a game watch remains active.")
        if submission_attempted:
            print("Submission may have reached the server; inspect before retrying.")
    except Exception as exc:
        print(f"Check test failed: {type(exc).__name__}: {exc}")
        if submission_attempted:
            print("Server acceptance may be unknown. No automatic resend.")
            print("Run inspect_ap_connection.py to inspect checked locations.")
        else:
            print("No LocationChecks command was attempted.")
        print("Press Ctrl+F3 if a game watch remains active.")
        raise SystemExit(1)
