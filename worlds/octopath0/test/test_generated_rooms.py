"""Generate independent solo rooms and exercise the CLI with simulated game responses."""
import asyncio
from functools import partial
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from websockets.legacy.server import serve
import MultiServer

WORLD = Path(__file__).resolve().parents[1]
with patch.object(sys, "path", [str(WORLD / "PythonSender"), *sys.path]):
    import ap_connection
    import deliver_ap_item
    import generated_room
    import save_binding
    import watch_chests


class GameBridge:
    def __init__(self):
        self.seed = None
        self.index = 0
        self.grants = 0
        self.token = None

    def publish(self, path, payload):
        path.write_text(payload)
        header, token, *args = payload.splitlines()
        if header == "OT0AP_BIND_V1":
            action, seed, team, slot, end = args
            if self.seed is None and action == "initialize":
                self.seed = seed
                status = "initialized"
            elif seed != self.seed:
                status = "mismatch"
            elif action == "authorize":
                self.token = token
                status = "authorized"
            else:
                status = "matched"
            path.with_name(token + ".binding").write_text("\n".join([
                "OT0AP_BIND_RESPONSE_V1", token, status, "game save", self.seed,
                team, slot, str(self.index), "test", end]))
        elif header == "OT0AP_BOUND_WATCH_V1":
            seed, team, slot, treasure, end = args
            matched = (seed, team, slot) == (self.seed, "0", "1")
            path.with_name(token + ".watch.0").write_text("\n".join([
                "OT0AP_LIVE_WATCH_V1", token, "game save", treasure, "complete" if matched else "error",
                treasure+"=checked" if matched else "unknown", "observation" if matched else "wrong save", end]))
        elif header == "OT0AP_BOUND_ITEM_V1":
            auth, seed, team, slot, start, item, end = args
            assert (auth, seed, team, slot, item) == (self.token, self.seed, "0", "1", "110001")
            assert int(start) == self.index
            self.grants += 1
            self.index += 1
            path.with_name(token + ".response").write_text("\n".join([
                "OT0AP_RESPONSE_V1", token, "processed", str(self.index), "game save", "test", end]))
        else:
            raise AssertionError(header)


class GeneratedRoomsTest(unittest.IsolatedAsyncioTestCase):
    async def test_two_rooms_crossed_saves(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, LOCALAPPDATA=directory):
            games = [GameBridge(), GameBridge()]
            for number in (112001, 112002):
                subprocess.run([sys.executable, "Generate.py", "--seed", str(number), "--spoiler", "0",
                                "--player_files_path", str(WORLD / "Players_OT0TwoChest"),
                                "--outputpath", directory], check=True, cwd=WORLD.parents[1],
                               env={**os.environ, "SKIP_REQUIREMENTS_UPDATE": "1"})
            rooms = []
            for archive in sorted(Path(directory).glob("*.zip")):
                ctx = MultiServer.Context("127.0.0.1", 0, None, None, 1, 10, False)
                ctx.load(str(archive))
                ctx.init_save(False)
                server = await self.enterAsyncContext(serve(partial(MultiServer.server, ctx=ctx), "127.0.0.1", 0))
                rooms.append((ctx, f"ws://127.0.0.1:{server.sockets[0].getsockname()[1]}"))
            self.assertEqual(len(rooms), 2)
            self.assertNotEqual(rooms[0][0].seed_name, rooms[1][0].seed_name)

            async def run(i, game, *command):
                ctx, address = rooms[i]
                with (
                    patch.object(ap_connection, "SERVER", address),
                    patch.object(save_binding, "publish", game.publish),
                    patch.object(watch_chests, "publish", game.publish),
                    patch.object(deliver_ap_item, "publish", game.publish),
                ):
                    return await asyncio.to_thread(generated_room.main, ["--seed", ctx.seed_name, *command])

            for i, game in enumerate(games):
                await run(i, game, "initialize")
                await run(i, game, "inspect")
            for i, game in enumerate(games):
                ctx = rooms[i][0]
                other = games[1-i]
                with self.assertRaisesRegex(RuntimeError, "Stored seed mismatch"):
                    await run(i, other, "inspect")
                with self.assertRaisesRegex(RuntimeError, "wrong save"):
                    await run(i, other, "check", "70115")
                self.assertEqual(ctx.location_checks[0, 1], set())
                await run(i, game, "check", "70115")
                self.assertEqual(ctx.location_checks[0, 1], {10070115})
                prior = other.grants
                self.assertEqual(await run(i, other, "deliver"), 1)
                self.assertEqual(other.grants, prior)
                self.assertEqual(await run(i, game, "deliver"), 0)
                self.assertEqual(await run(i, game, "deliver"), 0)
                self.assertEqual((game.grants, game.index), (1, 1))
