"""Bind a save, check a chest or deliver a shield in a generated solo two-chest room."""
import argparse
import asyncio
import os
from pathlib import Path
import re
import runpy

from ap_connection import expect, verified_connection
from deliver_ap_item import run_cli as deliver
from save_binding import request_save_binding
from submit_two_chest import run as check_chest


def package_id(row, field, catalog):
    value = row.get(field)
    if type(value) is not int or value <= 0:
        raise RuntimeError(f"Invalid {field}.")
    expect(f"Data-package mapping for {row['name']}", catalog.get(row["name"]), value)
    return value


class GeneratedRoom:
    def __init__(self, seed, player):
        if not re.fullmatch(r"[0-9]{1,64}", seed):
            raise ValueError("Use the numeric seed name printed by the server.")
        self.seed = seed
        self.player = player
        self.slot_data = None
        world = Path(__file__).resolve().parents[1]
        self.chests = runpy.run_path(str(world / "locations.py"))["CHEST_BY_TREASURE"]

    def validate_slot(self, data, package):
        if not isinstance(data, dict):
            raise RuntimeError("Missing versioned slot data.")
        expect("Two-chest schema", data.get("prototype_schema"), 2)
        expect("Two-chest goal", data.get("prototype_goal"), "receive_two_small_shields")
        locations = data.get("locations")
        if not isinstance(locations, list) or len(locations) != 2:
            raise RuntimeError("Expected two enabled chest rows.")
        treasures, ap_ids = set(), set()
        for row in locations:
            treasure = row.get("game_treasure_id") if isinstance(row, dict) else None
            if type(treasure) is not int or treasure not in (70115, 70117):
                raise RuntimeError("Unsupported game treasure.")
            expect("Chest name for game treasure", row.get("name"), self.chests[treasure][1])
            ap_ids.add(package_id(row, "ap_location_id", package["location_name_to_id"]))
            treasures.add(treasure)
        if len(treasures) != 2 or len(ap_ids) != 2:
            raise RuntimeError("Duplicate game treasure or AP location.")
        items = data.get("items")
        if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
            raise RuntimeError("Expected one supported item mapping.")
        item = items[0]
        expect("Supported shield grant", [item.get(k) for k in ("name", "game_item_id", "quantity")],
               ["Small Shield", 110001, 1])
        package_id(item, "ap_item_id", package["item_name_to_id"])
        if self.slot_data is not None:
            expect("Slot data on reconnect", data, self.slot_data)

    async def verify(self, callback=None):
        async def capture(ws, checked, data):
            self.slot_data = data
            if callback is not None:
                await callback(ws, checked, data)
        return await verified_connection(self.seed, self.player, None, capture, validate_slot=self.validate_slot)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, help="Server seed name, including leading zeroes.")
    parser.add_argument("--player", default="OT0TwoChest")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("inspect")
    actions.add_parser("initialize")
    actions.add_parser("check").add_argument("treasure", choices=(70115, 70117), type=int)
    actions.add_parser("deliver")
    args = parser.parse_args(argv)
    room = GeneratedRoom(args.seed, args.player)
    if args.action == "deliver":
        return deliver([], room=room)
    if args.action == "check":
        folder = Path(os.environ["LOCALAPPDATA"]) / "OctopathArchipelagoBridge"
        asyncio.run(check_chest(args.treasure, folder, room=room))
    else:
        request_save_binding(args.action, room=room)
        for row in room.slot_data["locations"]:
            print(f"{row['name']}: treasure {row['game_treasure_id']} -> AP {row['ap_location_id']}")
        item = room.slot_data["items"][0]
        print(f"{item['name']}: AP {item['ap_item_id']} -> game {item['game_item_id']}, quantity {item['quantity']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Exception, KeyboardInterrupt) as exc:
        raise SystemExit(f"Stopped: {exc}. Ctrl+F3 disarms the bridge.")
