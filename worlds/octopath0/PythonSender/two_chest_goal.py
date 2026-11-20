"""Inspect or report the receive-two-shields goal in the shipped revised room."""
import argparse
import asyncio
import json

from ap_connection import expect, receive_command
from ap_history import inspect_history
from save_binding import request_save_binding
from two_chest_profiles import REVISED_SEED, verify_revised_room


STATUS_KEY = "_read_client_status_0_1"
CLIENT_GOAL = 30


async def read_status(ws):
    await ws.send(json.dumps([{"cmd": "Get", "keys": [STATUS_KEY]}]))
    reply = await receive_command(ws, "Retrieved")
    keys = reply.get("keys")
    value = keys.get(STATUS_KEY) if isinstance(keys, dict) else None
    if type(value) is not int or value not in (0, 5, 10, 20, CLIENT_GOAL):
        raise RuntimeError("Server did not return a recognized status for team 0, slot 1.")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-goal", action="store_true",
                        help="Inspect the bound save and mark the verified slot complete.")
    report = parser.parse_args(argv).report_goal
    complete = False

    async def preflight(ws, checked, slot):
        nonlocal complete
        complete = await read_status(ws) == CLIENT_GOAL
        if complete:
            print("Goal already complete on server.")
        elif report:
            expected = [row["ap_location_id"] for row in slot["locations"]]
            expect("Both chests checked", sorted(checked), sorted(expected))
        else:
            print("Goal pending on server.")

    asyncio.run(verify_revised_room(preflight))
    if complete or not report:
        return

    print("Goal report requested. Select the reloaded test save for inspection. "
          "Its delivery index must be 2.", flush=True)
    binding = request_save_binding("inspect", revised=True)
    if binding is None:
        raise RuntimeError("The selected save has no binding.")
    expect("Goal save identity and delivery progress",
           [binding["seed"], binding["team"], binding["slot"], binding["next_index"]],
           [REVISED_SEED, 0, 1, 2])

    async def finish(ws, checked, slot):
        history = await inspect_history(ws, checked, revised=True)
        expect("Two delivered shield entries", len(history), binding["next_index"])
        if await read_status(ws) == CLIENT_GOAL:
            print("Goal already complete on server.")
            return
        try:
            await ws.send(json.dumps([{"cmd": "StatusUpdate", "status": CLIENT_GOAL}]))
            expect("Server goal confirmation", await read_status(ws), CLIENT_GOAL)
        except (Exception, asyncio.CancelledError):
            print("Goal outcome unconfirmed. Run two_chest_goal.py without arguments to read server status.")
            raise
        print("CONFIRMED: two-shield goal complete on server.", flush=True)

    asyncio.run(verify_revised_room(finish))


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        raise SystemExit(f"Goal command stopped: {exc}")
