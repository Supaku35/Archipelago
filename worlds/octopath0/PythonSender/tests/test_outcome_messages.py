"""Offline checks for outcome reporting; no AP/game access."""
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bridge_io
import deliver_ap_item as delivery
import save_binding


class DeliveryMessages(unittest.TestCase):
    def run_command(self, *, progress=0, binding_error=None, publish_error=None,
                    response_error=None, response_index=1, args=None):
        async def history(*, revised):
            assert not revised
            return [{"item": 10000002, "location": 10000001, "player": 1, "flags": 1}]
        binding = {"seed": delivery.SEED, "team": 0, "slot": 1,
                   "next_index": progress, "token": "a" * 32, "save_name": "save A"}
        with patch.object(delivery, "read_verified_history", history), patch.object(delivery, "request_save_binding", return_value=binding, side_effect=binding_error), patch.object(delivery, "publish", side_effect=publish_error) as publish, patch.object(delivery, "wait_for_bridge_response", return_value=(response_index, "save A"), side_effect=response_error) as wait, patch.dict(os.environ, {"LOCALAPPDATA": "unused-mocked-bridge"}), contextlib.redirect_stdout(io.StringIO()) as output:
            result = delivery.run_cli(args or [])
        return result, output.getvalue(), publish.call_count, wait.call_count

    def test_confirmed_cancellation_has_no_uncertainty_warning(self):
        code, out, sends, waits = self.run_command(response_error=bridge_io.BridgeCancelled("cancelled"))
        self.assertEqual((code, sends, waits), (1, 1, 1))
        self.assertIn("No grant or progress change for the cancelled request", out)
        self.assertNotIn("may already", out)
        self.assertNotIn("not confirmed", out)

    def test_binding_failure_does_not_claim_delivery_was_attempted(self):
        code, out, sends, waits = self.run_command(binding_error=RuntimeError("halted"))
        self.assertEqual((code, sends, waits), (1, 0, 0))
        self.assertIn("did not attempt to publish", out)
        self.assertNotIn("may already", out)

    def test_publication_failure_remains_uncertain(self):
        code, out, sends, waits = self.run_command(publish_error=OSError("replace failed"))
        self.assertEqual((code, sends, waits), (1, 1, 0))
        self.assertIn("Delivery outcome is not confirmed", out)
        self.assertIn("may already have been applied", out)

    def test_blocked_timeout_and_invalid_counter_remain_uncertain(self):
        for kwargs in [{"response_error": RuntimeError("blocked")},
                       {"response_error": TimeoutError("timeout")},
                       {"response_index": 0}]:
            with self.subTest(kwargs=kwargs):
                code, out, sends, waits = self.run_command(**kwargs)
                self.assertEqual((code, sends, waits), (1, 1, 1))
                self.assertIn("not confirmed", out)
                self.assertNotIn("No grant or progress change", out)

    def test_interrupt_before_and_after_publication(self):
        for key, sends in [("binding_error", 0), ("response_error", 1)]:
            with self.subTest(stage=key):
                code, out, actual, _ = self.run_command(**{key: KeyboardInterrupt()})
                self.assertEqual((code, actual), (0, sends))
                self.assertIn("did not attempt" if not sends else "not confirmed", out)

    def test_caught_up_sends_nothing(self):
        code, out, sends, waits = self.run_command(progress=1)
        self.assertEqual((code, sends, waits), (0, 0, 0))
        self.assertIn("Already caught up", out)

    def test_success_and_replay_keep_existing_flow(self):
        for progress, args in [(0, []), (1, ["--replay-index-zero"])]:
            with self.subTest(progress=progress):
                code, out, sends, waits = self.run_command(progress=progress, args=args)
                self.assertEqual((code, sends, waits), (0, 1, 1))
                self.assertIn("accounted for in memory", out)


class BridgeCancellationTests(unittest.TestCase):
    def test_only_valid_cancelled_response_raises_typed_cancellation(self):
        rid = "a" * 32
        for status, response_id, exception in [
            ("cancelled", rid, bridge_io.BridgeCancelled),
            ("blocked", rid, RuntimeError),
            ("cancelled", "b" * 32, RuntimeError),
        ]:
            with self.subTest(status=status, response_id=response_id), tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
                folder = Path(tmp)
                (folder / "inbox.txt").write_text(f"OT0AP_LIVE_V1\n{rid}\n")
                (folder / f"{rid}.response").write_text(
                    f"OT0AP_RESPONSE_V1\n{response_id}\n{status}\nunknown\nunknown\ndetail\nEND\n"
                )
                with self.assertRaises(exception) as caught:
                    bridge_io.wait_for_bridge_response(folder, rid, "processed", 1)
                self.assertIs(type(caught.exception), exception)


class BindingMessages(unittest.TestCase):
    def run_binding(self, operation, status):
        async def verify():
            return {10000001}
        def publish(path, text):
            path.write_text(text)
            rid = text.splitlines()[1]
            (path.parent / f"{rid}.binding").write_text(
                f"OT0AP_BIND_RESPONSE_V1\n{rid}\n{status}\nsave A\n"
                f"{save_binding.SEED}\n0\n1\n0\ndetail\nEND\n"
            )
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"LOCALAPPDATA": tmp}), patch.object(save_binding, "inspect_connection", verify), patch.object(save_binding, "publish", publish), contextlib.redirect_stdout(io.StringIO()) as output:
            result = save_binding.request_save_binding(operation)
        return result, output.getvalue()

    def test_only_initialization_prompts_to_save(self):
        for operation, status in [("initialize", "initialized"), ("initialize", "matched"),
                                  ("inspect", "matched"), ("authorize", "authorized")]:
            with self.subTest(operation=operation, status=status):
                result, output = self.run_binding(operation, status)
                self.assertEqual(result["next_index"], 0)
                self.assertEqual("Save normally" in output, status == "initialized")
                if operation == "inspect":
                    self.assertNotIn("requires exploration", output)
                if operation == "authorize":
                    self.assertIn("Authorization only", output)


if __name__ == "__main__":
    unittest.main()

