"""Offline regression tests. No game, AP server, or real bridge directory is used."""
import asyncio
import contextlib
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ap_connection
import ap_history
import chest_checks


class FakeSocket:
    def __init__(self, packets):
        self.frames = list(packets)
        self.sent = []

    async def send(self, value):
        self.sent.append(json.loads(value))

    async def recv(self):
        if not self.frames:
            raise AssertionError("Unexpected additional network read")
        return json.dumps(self.frames.pop(0))


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.item = dict(ap_history.EXPECTED_ITEM)
        self.packet = {"cmd": "ReceivedItems", "index": 0, "items": [self.item]}

    def test_list_and_dictionary_items(self):
        for item in [self.item, [10000002, 10000001, 1, 1]]:
            with self.subTest(item=item):
                self.assertEqual(
                    ap_history.validate_history({"index": 0, "items": [item]}),
                    [self.item],
                )

    def test_rejects_wrong_index_size_types_and_mapping(self):
        packets = [
            {"index": 1, "items": [self.item]},
            {"index": False, "items": [self.item]},
            {"index": 0, "items": [{**self.item, "player": True}]},
            {"index": 0, "items": [{**self.item, "item": 999}]},
            {"index": 0, "items": [{**self.item, "flags": 1.0}]},
        ]
        for packet in packets:
            with self.subTest(packet=packet), self.assertRaises(RuntimeError):
                ap_history.validate_history(packet)

    def test_duplicate_snapshots_report_history_once(self):
        ws = FakeSocket([[self.packet, self.packet]])
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = asyncio.run(ap_history.inspect_history(ws, {10000001}))
        self.assertEqual(result, [self.item])
        self.assertEqual(output.getvalue().count("HISTORY VERIFIED"), 1)
        self.assertEqual(ws.sent, [[
            {"cmd": "ConnectUpdate", "items_handling": 7}, {"cmd": "Sync"},
        ]])

    def test_invalid_second_snapshot_is_not_ignored(self):
        ws = FakeSocket([[self.packet, {**self.packet, "index": 1}]])
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            asyncio.run(ap_history.inspect_history(ws, {10000001}))

    def test_pending_and_caught_up_without_mutating_history(self):
        history = [dict(self.item)]
        self.assertEqual(ap_history.plan_pending(history, 0), [(0, self.item)])
        self.assertEqual(ap_history.plan_pending(history, 1), [])
        self.assertEqual(history, [self.item])
        for progress in [-1, 2, True, 0.0, "0", None]:
            with self.subTest(progress=progress), self.assertRaises(RuntimeError):
                ap_history.plan_pending(history, progress)

    def test_shared_reader_uses_verified_connection_callback(self):
        ws = FakeSocket([[self.packet]])
        async def verified(after_verified):
            await after_verified(ws, {10000001})
        with patch.object(ap_history, "inspect_connection", verified), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(asyncio.run(ap_history.read_verified_history()), [self.item])

    def test_wrong_checked_locations_abort_before_request(self):
        ws = FakeSocket([])
        with self.assertRaises(RuntimeError):
            asyncio.run(ap_history.inspect_history(ws, set()))
        self.assertEqual(ws.sent, [])


class ChestTests(unittest.TestCase):
    def run_watch(self, events, dry_run=False, timeout=600):
        published = []
        def publish(path, text):
            published.append(text)
            path.write_text(text, encoding="utf-8")
            token = text.splitlines()[1]
            for sequence, event in enumerate(events):
                if isinstance(event, bytes):
                    data = event
                else:
                    status, observation, save = event
                    data = ("\n".join([
                        "OT0AP_WATCH_V1", token, save, "70117", status,
                        observation, "test detail", "END",
                    ]) + "\n").encode()
                (path.parent / f"{token}.watch.{sequence}").write_bytes(data)
        ticks = iter(range(100))
        with tempfile.TemporaryDirectory() as folder, patch.object(chest_checks, "publish", publish), patch.object(chest_checks.time, "sleep"), patch.object(chest_checks.time, "monotonic", side_effect=lambda: next(ticks)), contextlib.redirect_stdout(io.StringIO()) as output:
            result = chest_checks.run_checks_watch(Path(folder), timeout, dry_run)
        self.assertEqual(len(published), 1)
        self.assertTrue(published[0].startswith("OT0AP_WATCH_QUERY_V1\n"))
        return result, output.getvalue()

    def test_completed_watch_and_dry_run(self):
        result, output = self.run_watch([
            ("watching", "not_detected", "save A"),
            ("complete", "checked", "save A"),
        ], dry_run=True)
        self.assertEqual(result["treasure_id"], 70117)
        self.assertEqual(result["save"], "save A")
        self.assertEqual(result["status"], "complete")
        self.assertIn('[{"cmd": "LocationChecks", "locations": [10000001]}]', output)

    def test_cancellation_returns_no_evidence(self):
        result, _ = self.run_watch([
            ("watching", "not_detected", "save A"),
            ("stopped", "unknown", "save A"),
        ])
        self.assertIsNone(result)

    def test_blocked_error_and_save_change_reject_evidence(self):
        for event in [
            ("blocked", "unknown", "save A"),
            ("error", "unknown", "save A"),
            ("complete", "checked", "save B"),
        ]:
            with self.subTest(event=event), self.assertRaises(RuntimeError):
                self.run_watch([("watching", "not_detected", "save A"), event])

    def test_invalid_completion_and_missing_identity_rejected(self):
        for event in [
            ("complete", "not_detected", "save A"),
            ("watching", "checked", "save A"),
            ("complete", "checked", "unknown"),
        ]:
            with self.subTest(event=event), self.assertRaises(RuntimeError):
                self.run_watch([event])

    def test_oversized_event_and_timeout_fail(self):
        with self.assertRaises(RuntimeError):
            self.run_watch([b"x" * 8193])
        with self.assertRaises(RuntimeError):
            self.run_watch([], timeout=1)

    def test_preview_requires_known_completed_check(self):
        location, commands = chest_checks.build_location_check_preview(
            "treasure", 70117, "complete", "checked"
        )
        self.assertEqual(location["ap_location_id"], 10000001)
        self.assertEqual(commands, [{"cmd": "LocationChecks", "locations": [10000001]}])
        for args in [
            ("treasure", 70117, "stopped", "unknown"),
            ("treasure", 70117, "complete", "not_detected"),
            ("treasure", 999, "complete", "checked"),
        ]:
            with self.subTest(args=args), self.assertRaises(RuntimeError):
                chest_checks.build_location_check_preview(*args)

    def test_snapshot_checked_and_error_file(self):
        for failure in [False, True]:
            def publish(path, text):
                path.write_text(text, encoding="utf-8")
                token = text.splitlines()[1]
                if failure:
                    (path.parent / f"{token}.checks-error").write_text("test failure")
                else:
                    (path.parent / f"{token}.checks").write_text(
                        f"OT0AP_CHECKS_V2\n{token}\ntreasure\nsave A\n70117\nchecked\nEND\n"
                    )
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder, patch.object(chest_checks, "publish", publish), contextlib.redirect_stdout(io.StringIO()) as output:
                if failure:
                    with self.assertRaises(RuntimeError):
                        chest_checks.run_checks_test(Path(folder), 1)
                else:
                    chest_checks.run_checks_test(Path(folder), 1)
                    self.assertIn("Observation: checked", output.getvalue())


class ConnectionAndImportTests(unittest.TestCase):
    def test_connection_reader_rejects_unexpected_item_packets(self):
        ws = FakeSocket([[{"cmd": "Connected"}, {"cmd": "ReceivedItems"}]])
        with self.assertRaises(RuntimeError):
            asyncio.run(ap_connection.receive_command(ws, "Connected"))

    def test_commands_import_without_connecting_or_publishing(self):
        with patch.object(ap_connection, "connect", side_effect=AssertionError("network on import")), patch("bridge_io.publish", side_effect=AssertionError("publication on import")):
            for name in [
                "bind_ap_save", "deliver_ap_item", "inspect_ap_connection",
                "inspect_ap_items", "reconcile_ap_items", "send_test_batch",
                "submit_chest_check",
            ]:
                importlib.reload(importlib.import_module(name))


if __name__ == "__main__":
    unittest.main()

