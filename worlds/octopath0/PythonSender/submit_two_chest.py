"""Submit one observed chest to the pinned OT0TwoChest test room."""
import argparse
import asyncio
import json
import os
from pathlib import Path

from ap_connection import receive_command, verified_connection
from watch_chests import observe_watch


# This describes the shipped archive, independently of current world definitions.
SEED = "74188682935974291198"
PLAYER = "OT0TwoChest"
SLOT_DATA = {
    "prototype_schema": 2,
    "prototype_goal": "receive_two_small_shields",
    "locations": [
        {"name": "Cerulean Caverns - Southwest Cliff Chest",
         "ap_location_id": 10000001, "game_treasure_id": 70117},
        {"name": "Wishvale Trail - West near Squirrel",
         "ap_location_id": 10170115, "game_treasure_id": 70115},
    ],
    "items": [{"name": "Small Shield", "ap_item_id": 10000002,
               "game_item_id": 110001, "quantity": 1}],
}


REVISED_SEED = "84576831886948881492"
REVISED_SLOT_DATA = {
    "prototype_schema": 2,
    "prototype_goal": "receive_two_small_shields",
    "locations": [
        {"name": "Cerulean Caverns - Southwest Cliff Chest",
         "ap_location_id": 10070117, "game_treasure_id": 70117},
        {"name": "Wishvale Trail - West Stump Chest",
         "ap_location_id": 10070115, "game_treasure_id": 70115},
    ],
    "items": [{"name": "Small Shield", "ap_item_id": 10110001,
               "game_item_id": 110001, "quantity": 1}],
}
# SHA-256 of the revised archive's full name-to-ID map in sorted compact JSON.
REVISED_CATALOG_DIGEST = "af5485eb136acb4c62f4c7878b0d52031c8486aa1270485139f2eb7d9fa5578b"
PROFILES = {
    "original": (SEED, SLOT_DATA, None),
    "revised": (REVISED_SEED, REVISED_SLOT_DATA, REVISED_CATALOG_DIGEST),
}


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
