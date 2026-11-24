"""Verified AP connection and prototype identity checks; no action on import."""

import asyncio
import json
import hashlib
import uuid

from websockets import connect


SERVER = "ws://127.0.0.1:38281"
GAME = "Octopath Traveler 0"
PLAYER = "OT0Prototype"
SEED = "02053695854357871005"
LOCATION = "Cerulean Caverns - Southwest Cliff Chest"

EXPECTED_SLOT_DATA = {
    "prototype_schema": 1,
    "prototype_goal": "receive_small_shield",
    "locations": [{
        "name": LOCATION,
        "ap_location_id": 10000001,
        "game_treasure_id": 70117,
    }],
    "items": [{
        "name": "Small Shield",
        "ap_item_id": 10000002,
        "game_item_id": 110001,
        "quantity": 1,
    }],
}


def expect(label, actual, expected):
    # JSON comparison also distinguishes booleans/floats from integer IDs.
    if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise RuntimeError(
            f"{label} mismatch: expected {expected!r}, received {actual!r}"
        )


async def receive_command(ws, wanted):
    while True:
        packets = json.loads(await ws.recv())
        if not isinstance(packets, list) or not all(
            isinstance(packet, dict) for packet in packets
        ):
            raise RuntimeError("Invalid server packet envelope.")

        for packet in packets:
            command = packet.get("cmd")
            if command in {"ConnectionRefused", "InvalidPacket"}:
                raise RuntimeError(f"Server rejected inspection: {packet!r}")
            if command == "ReceivedItems":
                raise RuntimeError("Unexpected item packet; nothing applied.")

        matches = [p for p in packets if p.get("cmd") == wanted]
        if len(matches) > 1:
            raise RuntimeError(f"Duplicate {wanted} response.")
        if matches:
            return matches[0]

async def verified_connection(seed, player, slot_data, after_verified=None, *, legacy_catalog=False, catalog_digest=None, validate_slot=None):
    async with asyncio.timeout(30):
        async with connect(
            SERVER, open_timeout=10, close_timeout=5, max_size=1_048_576
        ) as ws:
            room = await receive_command(ws, "RoomInfo")
            expect("Seed", room.get("seed_name"), seed)
            if GAME not in room.get("games", []):
                raise RuntimeError("Expected game is absent from this room.")
            if room.get("password"):
                raise RuntimeError("This inspector expects the passwordless local room.")

            print(f"Seed verified: {seed}", flush=True)

            await ws.send(json.dumps([{
                "cmd": "GetDataPackage",
                "games": [GAME],
            }]))
            package = await receive_command(ws, "DataPackage")
            game_data = package.get("data", {}).get("games", {}).get(GAME, {})
            if validate_slot is None:
                expected_catalog = {row["name"]: row["ap_location_id"] for row in slot_data["locations"]}
                item_catalog = {row["name"]: row["ap_item_id"] for row in slot_data["items"]}
                # A seed stores the game-wide catalog from its generation. Both
                # catalogs can describe a schema-1 slot with just the cavern chest.
                catalog = game_data.get("location_name_to_id")
                trail = "Wishvale Trail - West near Squirrel"
                if legacy_catalog and isinstance(catalog, dict) and trail in catalog:
                    expected_catalog[trail] = 10170115
                if catalog_digest is None:
                    expect("Location catalog", catalog, expected_catalog)
                else:
                    if not isinstance(catalog, dict):
                        raise RuntimeError("Missing location catalog.")
                    serialized = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
                    expect("Pinned location catalog", hashlib.sha256(serialized).hexdigest(), catalog_digest)
                    for name, ap_id in expected_catalog.items():
                        expect(name, catalog.get(name), ap_id)
                expect(
                    "Item catalog", game_data.get("item_name_to_id"),
                    item_catalog,
                )

            await ws.send(json.dumps([{
                "cmd": "Connect",
                "password": None,
                "game": GAME,
                "name": player,
                "uuid": uuid.uuid4().hex,
                "version": {
                    "major": 0, "minor": 6, "build": 9, "class": "Version",
                },
                "items_handling": 0,
                "tags": ["AP"],
                "slot_data": True,
            }]))
            connected = await receive_command(ws, "Connected")
            expect("Team", connected.get("team"), 0)
            expect("Slot", connected.get("slot"), 1)

            slot_info = connected.get("slot_info", {}).get("1", {})
            expect("Player name", slot_info.get("name"), player)
            expect("Game", slot_info.get("game"), GAME)
            received_slot = connected.get("slot_data")
            if validate_slot is not None:
                expect("Solo player slots", list(connected["slot_info"]), ["1"])
                validate_slot(received_slot, game_data)
            else:
                expect("Slot data", received_slot, slot_data)
            slot_ids = sorted(row["ap_location_id"] for row in received_slot["locations"])
            print("Data-package mappings verified.", flush=True)

            missing = connected.get("missing_locations")
            checked = connected.get("checked_locations")
            for label, values in (("missing_locations", missing),
                                  ("checked_locations", checked)):
                if not isinstance(values, list) or any(
                    type(value) is not int for value in values
                ):
                    raise RuntimeError(f"Invalid {label}.")
                if len(values) != len(set(values)):
                    raise RuntimeError(f"Duplicate IDs in {label}.")

            if set(missing) & set(checked):
                raise RuntimeError("Location is both checked and missing.")
            expect("Slot location set", sorted(missing + checked), slot_ids)

            print(f"Slot verified: team 0, slot 1, player {player}", flush=True)
            print("Slot schema, goal, and game-ID mappings verified.", flush=True)
            print(f"Missing locations: {missing}", flush=True)
            print(f"Checked locations: {checked}", flush=True)

            if after_verified is not None:
                await after_verified(ws, set(checked), connected["slot_data"])

    if after_verified is None:
        print("AP connection verified and closed. This inspection submitted no checks, granted no items, and reported no goal.")
    else:
        print("Verified session closed.")

    return set(checked)


async def inspect_connection(after_verified=None):
    async def legacy_callback(ws, checked, slot_data):
        await after_verified(ws, checked)

    return await verified_connection(SEED, PLAYER, EXPECTED_SLOT_DATA,
                                     legacy_callback if after_verified else None,
                                     legacy_catalog=True)
