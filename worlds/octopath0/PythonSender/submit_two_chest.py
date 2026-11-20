"""Submit one observed chest to the pinned OT0TwoChest test room."""
import argparse
import asyncio
import json
import os
from pathlib import Path

from ap_connection import receive_command, verified_connection
from two_chest_profiles import (PLAYER, PROFILES, REVISED_CATALOG_DIGEST, REVISED_SEED,
                                REVISED_SLOT_DATA, SEED, SLOT_DATA)
from watch_chests import observe_watch


def location_map(slot_data):
    return {row["game_treasure_id"]: row["ap_location_id"] for row in slot_data["locations"]}


async def run(treasure, folder, timeout=600, *, profile="original"):
    seed, expected_slot, digest = PROFILES[profile]
    observed = False
    attempted = False
    pending = False

    async def check(ws, checked, slot_data):
        nonlocal pending, attempted
        locations = location_map(slot_data)
        target = locations[treasure]
        if target in checked:
            print(f"Already checked on server: {target}. Skipped.")
            return
        if not observed:
            pending = True
            return
        attempted = True
        await ws.send(json.dumps([{"cmd": "LocationChecks", "locations": [target]}]))
        print(f"SUBMITTED {target}. Waiting for server confirmation.", flush=True)
        while True:
            packet = await receive_command(ws, "RoomUpdate")
            if "checked_locations" not in packet:
                continue
            ids = packet["checked_locations"]
            if (not isinstance(ids, list) or any(type(i) is not int for i in ids)
                    or len(set(ids)) != len(ids) or not set(ids).issubset(locations.values())):
                raise RuntimeError("Invalid checked locations in confirmation.")
            if target in ids:
                print(f"CONFIRMED {target}.", flush=True)
                return

    await verified_connection(seed, PLAYER, expected_slot, check, catalog_digest=digest)
    if not pending:
        return
    folder.mkdir(parents=True, exist_ok=True)
    evidence = observe_watch(folder, timeout, [treasure], live=True)
    if evidence is None:
        print("Cancelled. Nothing submitted.")
        return
    if not evidence.finished or evidence.checked != {treasure} or not evidence.save:
        raise RuntimeError("Missing completed bound-watch evidence.")
    print(f"Verified treasure {treasure} on {evidence.save}. Rechecking room.", flush=True)
    observed = True
    try:
        await verified_connection(seed, PLAYER, expected_slot, check, catalog_digest=digest)
    except (Exception, asyncio.CancelledError, KeyboardInterrupt):
        if attempted:
            print("Submission outcome uncertain. Inspect !checked before retrying. No automatic resend.")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submit-treasure", required=True, type=int, choices=tuple(location_map(SLOT_DATA)))
    parser.add_argument("--profile", choices=tuple(PROFILES), default="original")
    args = parser.parse_args()
    folder = Path(os.environ["LOCALAPPDATA"]) / "OctopathArchipelagoBridge"
    asyncio.run(run(args.submit_treasure, folder, profile=args.profile))


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        raise SystemExit(f"Stopped: {exc}. Ctrl+F3 stops any active game watch.")
