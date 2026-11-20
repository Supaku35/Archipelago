"""Revised fixture history, save inspection and initialization."""
import asyncio
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ap_history
import reconcile_ap_items as reconcile
import save_binding
from test_cleanup_helpers import FakeSocket
from two_chest_profiles import REVISED_SEED

END_SYNC = {"cmd": "DataPackage", "data": {"games": {}}}
TRAIL = [10110001, 10070115, 1, 1]
CAVERN = [10110001, 10070117, 1, 1]


def snapshot(items):
    return {"cmd": "ReceivedItems", "index": 0, "items": items}


def inspect(frames, checked):
    with redirect_stdout(StringIO()):
        return asyncio.run(ap_history.inspect_history(FakeSocket(frames), checked, revised=True))


class RevisedHistoryTests(unittest.TestCase):
    def test_empty_single_and_both_orders(self):
        for items in ([], [TRAIL], [CAVERN], [TRAIL, CAVERN], [CAVERN, TRAIL]):
            frames = [[snapshot(items)], [snapshot(items)]] if items else []
            sources = [item[1] for item in items]
            history = inspect([*frames, [END_SYNC]], set(sources))
            self.assertEqual([row["location"] for row in history], sources)

    def test_invalid_or_incomplete_snapshots(self):
        for items in ([], [TRAIL, TRAIL], [CAVERN], [[10000002, *TRAIL[1:]]],
                      [[*TRAIL[:2], 2, 1]], [[*TRAIL[:3], 0]]):
            with self.subTest(items=items), self.assertRaises(RuntimeError):
                inspect([[snapshot(items)], [END_SYNC]], {TRAIL[1]})
        with self.assertRaises(RuntimeError):
            inspect([[snapshot([TRAIL])], [snapshot([])], [END_SYNC]], {TRAIL[1]})

    def test_inspection_uses_loaded_index_and_detects_absence(self):
        history = inspect([[snapshot([TRAIL, CAVERN])], [END_SYNC]], {TRAIL[1], CAVERN[1]})
        for index, message in ((None, "next index is unknown"), (0, "Pending deliveries: 2"),
                               (1, "Pending deliveries: 1"), (2, "Pending deliveries: 0")):
            binding = None if index is None else dict(seed=REVISED_SEED, team=0, slot=1, next_index=index)
            with patch.object(reconcile, "read_verified_history", return_value=history), patch.object(
                    reconcile, "request_save_binding", return_value=binding) as query, redirect_stdout(StringIO()) as log:
                reconcile.main(["--profile", "revised"])
            query.assert_called_once_with("inspect", revised=True)
            self.assertIn(message, log.getvalue())

    def test_binding_requests_and_wrong_room(self):
        for operation, status, stored_seed in (("inspect", "matched", REVISED_SEED),
                                              ("initialize", "initialized", REVISED_SEED),
                                              ("inspect", "mismatch", "123")):
            def respond(path, data):
                header, token, action, seed, team, slot, end = data.splitlines()
                self.assertEqual((header, action, seed, team, slot, end),
                                 ("OT0AP_BIND_V1", operation, REVISED_SEED, "0", "1", "END"))
                path.write_text(data)
                path.with_name(token + ".binding").write_text(
                    f"OT0AP_BIND_RESPONSE_V1\n{token}\n{status}\nsave A\n{stored_seed}\n0\n1\n0\nobserved\nEND\n")
            with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, LOCALAPPDATA=tmp), patch.object(
                    save_binding, "verify_revised_room", new_callable=AsyncMock), patch.object(
                    save_binding, "publish", respond), redirect_stdout(StringIO()):
                if status == "mismatch":
                    with self.assertRaises(RuntimeError):
                        save_binding.request_save_binding(operation, revised=True)
                else:
                    result = save_binding.request_save_binding(operation, revised=True)
                    self.assertEqual((result["seed"], result["next_index"]), (REVISED_SEED, 0))
        with patch.object(save_binding, "verify_revised_room", side_effect=RuntimeError("wrong room")), patch.object(
                save_binding, "publish") as publish, self.assertRaises(RuntimeError):
            try:
                save_binding.request_save_binding("initialize", revised=True)
            finally:
                publish.assert_not_called()
