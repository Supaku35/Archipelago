"""Exercise the goal reporter against a pinned-room session with a mocked save."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import two_chest_goal as goal
from two_chest_profiles import REVISED_SEED, REVISED_SLOT_DATA


class Room:
    def __init__(self):
        self.checked = {10070115, 10070117}
        self.items = [[10110001, loc, 1, 1] for loc in sorted(self.checked)]
        self.status = 5
        self.updates = []
        self.replies = []
        self.sessions = 0

    async def verify(self, callback):
        self.sessions += 1
        await callback(self, self.checked, REVISED_SLOT_DATA)

    async def send(self, raw):
        for packet in json.loads(raw):
            if packet["cmd"] == "Get":
                self.replies.append({"cmd": "Retrieved", "keys": {goal.STATUS_KEY: self.status}})
            elif packet["cmd"] == "StatusUpdate":
                self.updates.append(packet)
                self.status = packet["status"]
            elif packet["cmd"] == "Sync":
                self.replies.append({"cmd": "ReceivedItems", "items": self.items, "index": 0})
            elif packet["cmd"] == "GetDataPackage":
                self.replies.append({"cmd": "DataPackage", "data": {"games": {}}})
            elif packet["cmd"] != "ConnectUpdate":
                raise AssertionError(packet)

    async def recv(self):
        return json.dumps([self.replies.pop(0)])


class GoalTests(unittest.TestCase):
    def setUp(self):
        self.room = Room()
        self.binding = dict(seed=REVISED_SEED, team=0, slot=1, next_index=2)
        self.enterContext(patch.object(goal, "verify_revised_room", self.room.verify))
        self.inspect = self.enterContext(patch.object(goal, "request_save_binding", return_value=self.binding))
        self.enterContext(redirect_stdout(StringIO()))

    def test_read_only_and_report_then_reconnect(self):
        goal.main([])
        self.assertFalse(self.room.updates)
        self.inspect.assert_not_called()
        goal.main(["--report-goal"])
        goal.main(["--report-goal"])
        goal.main([])
        self.assertEqual(self.room.updates, [{"cmd": "StatusUpdate", "status": 30}])
        self.inspect.assert_called_once_with("inspect", revised=True)

    def test_missing_chest(self):
        self.room.checked.remove(10070117)
        with self.assertRaises(RuntimeError):
            goal.main(["--report-goal"])
        self.inspect.assert_not_called()
        self.assertFalse(self.room.updates)

    def test_save_or_history_mismatch(self):
        for binding in (None, dict(self.binding, next_index=1), dict(self.binding, seed="other")):
            self.inspect.return_value = binding
            with self.assertRaises(RuntimeError):
                goal.main(["--report-goal"])
        self.inspect.return_value = self.binding
        self.room.items[1] = self.room.items[0]
        with self.assertRaises(RuntimeError):
            goal.main(["--report-goal"])
        self.assertFalse(self.room.updates)
