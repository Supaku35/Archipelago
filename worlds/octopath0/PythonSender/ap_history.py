"""Validated prototype item history and read-only reconciliation helpers."""

import asyncio
import json

from ap_connection import expect, inspect_connection


FIELDS = ("item", "location", "player", "flags")
EXPECTED_ITEM = {
    "item": 10000002,
    "location": 10000001,
    "player": 1,
    "flags": 1,
}


def validate_history(packet):
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
        expect("Supported AP item", item["item"], EXPECTED_ITEM["item"])
        history.append(item)
    return history


async def inspect_history(ws, checked):
    expect("Server checked locations", sorted(checked), [10000001])

    # Enable all item categories, then request the full history.
    await ws.send(json.dumps([
        {"cmd": "ConnectUpdate", "items_handling": 7},
        {"cmd": "Sync"},
    ]))
    print("Item history requested. Inspection only; no game bridge access.", flush=True)

    async with asyncio.timeout(20):
        while True:
            packets = json.loads(await ws.recv())
            if not isinstance(packets, list) or not all(
                isinstance(packet, dict) for packet in packets
            ):
                raise RuntimeError("Invalid server packet envelope.")

            verified = []
            for packet in packets:
                command = packet.get("cmd")
                if command in {"ConnectionRefused", "InvalidPacket"}:
                    raise RuntimeError(f"Server rejected item inspection: {packet!r}")
                if command == "ReceivedItems":
                    verified.append(validate_history(packet))

            if not verified:
                continue

            # Enabling items and Sync may produce identical full snapshots.
            # Validate every snapshot in this frame, but report history once.
            history = verified[0]
            if any(snapshot != history for snapshot in verified[1:]):
                raise RuntimeError("Conflicting full history snapshots; retry inspection.")
            print(f"HISTORY VERIFIED: packet index=0, item count={len(history)}", flush=True)
            for index, item in enumerate(history):
                print(f"AP delivery index {index}: {item}", flush=True)
            print("Mapped game item: Small Shield, ID 110001, quantity 1.", flush=True)
            print(f"Observed AP history length: {len(history)}. No delivery progress written.", flush=True)
            return history


async def read_verified_history():
    history = None

    async def capture(ws, checked):
        nonlocal history
        history = await inspect_history(ws, checked)

    await inspect_connection(after_verified=capture)
    if history is None:
        raise RuntimeError("No verified item history was returned.")
    return history


def plan_pending(history, next_index):
    # Validate the entire snapshot before planning any delivery.
    validate_history({"index": 0, "items": history})
    if type(next_index) is not int or not 0 <= next_index <= len(history):
        raise RuntimeError(
            "Saved live progress is invalid or exceeds verified history. "
            "Nothing reset or advanced."
        )
    return list(enumerate(history[next_index:], start=next_index))

