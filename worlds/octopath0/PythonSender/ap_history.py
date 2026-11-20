"""Validated prototype item history and read-only reconciliation helpers."""

import asyncio
import json

from ap_connection import expect, inspect_connection
from two_chest_profiles import REVISED_SLOT_DATA, verify_revised_room


FIELDS = ("item", "location", "player", "flags")
EXPECTED_ITEM = {
    "item": 10000002,
    "location": 10000001,
    "player": 1,
    "flags": 1,
}


def validate_history(packet, *, item_id=EXPECTED_ITEM["item"]):
    expect("ReceivedItems index", packet.get("index"), 0)

    items = packet.get("items")
    if not isinstance(items, list) or len(items) > 1_000_000:
        raise RuntimeError("Expected a full history of at most 1000000 items.")
    history = []
    for raw in items:
        if isinstance(raw, list) and len(raw) == 4:
            item = dict(zip(FIELDS, raw))
        elif isinstance(raw, dict):
            item = {field: raw.get(field) for field in FIELDS}
        else:
            raise RuntimeError("Unrecognized NetworkItem representation.")
        if any(type(value) is not int for value in item.values()):
            raise RuntimeError("NetworkItem fields must be integers.")
        # Source metadata varies; the grant allowlist remains Small Shield only.
        expect("Supported AP item", item["item"], item_id)
        history.append(item)
    return history


async def inspect_history(ws, checked, *, revised=False):
    item_id = EXPECTED_ITEM["item"]
    if revised:
        item_id = REVISED_SLOT_DATA["items"][0]["ap_item_id"]
    else:
        expect("Server checked locations", sorted(checked), [10000001])

    requests = [{"cmd": "ConnectUpdate", "items_handling": 7}, {"cmd": "Sync"}]
    if revised:
        # MultiServer omits ReceivedItems for empty histories. Its reply to the
        # following command marks the end of both ordered snapshot requests.
        requests.append({"cmd": "GetDataPackage", "games": []})
    await ws.send(json.dumps(requests))
    print("Item history requested. Inspection only; no game bridge access.", flush=True)

    history = None
    finished = False
    async with asyncio.timeout(20):
        while True:
            packets = json.loads(await ws.recv())
            if not isinstance(packets, list) or not all(
                isinstance(packet, dict) for packet in packets
            ):
                raise RuntimeError("Invalid server packet envelope.")

            for packet in packets:
                command = packet.get("cmd")
                if command in {"ConnectionRefused", "InvalidPacket"}:
                    raise RuntimeError(f"Server rejected item inspection: {packet!r}")
                if command == "ReceivedItems":
                    snapshot = validate_history(packet, item_id=item_id)
                    if history is not None and snapshot != history:
                        raise RuntimeError("Conflicting full history snapshots; retry inspection.")
                    history = snapshot
                elif revised and command == "DataPackage":
                    expect("End of history query", packet.get("data"), {"games": {}})
                    finished = True

            if revised:
                if not finished:
                    continue
                if history is None:
                    history = []
                # The shipped solo room places one progression shield at each
                # chest and has no starting items. Keep server order for indices.
                sources = []
                for item in history:
                    expect("Source slot", item["player"], 1)
                    expect("Shield flags", item["flags"], 1)
                    sources.append(item["location"])
                expect("Shield sources for checked chests", sorted(sources), sorted(checked))
            elif history is None:
                continue
            print(f"HISTORY VERIFIED: packet index=0, item count={len(history)}", flush=True)
            for index, item in enumerate(history):
                print(f"AP delivery index {index}: {item}", flush=True)
            print("Mapped game item: Small Shield, ID 110001, quantity 1.", flush=True)
            print(f"Observed AP history length: {len(history)}. No delivery progress written.", flush=True)
            return history


async def read_verified_history(*, revised=False):
    history = None

    async def capture(ws, checked, slot_data=None):
        nonlocal history
        history = await inspect_history(ws, checked, revised=revised)

    if revised:
        await verify_revised_room(capture)
    else:
        await inspect_connection(after_verified=capture)
    if history is None:
        raise RuntimeError("No verified item history was returned.")
    return history


def plan_pending(history, next_index, *, item_id=EXPECTED_ITEM["item"]):
    # Validate the entire snapshot before planning any delivery.
    validate_history({"index": 0, "items": history}, item_id=item_id)
    if type(next_index) is not int or not 0 <= next_index <= len(history):
        raise RuntimeError(
            "Saved live progress is invalid or exceeds verified history. "
            "Nothing reset or advanced."
        )
    return list(enumerate(history[next_index:], start=next_index))


