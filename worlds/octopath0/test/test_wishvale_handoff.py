"""Exercise the one-shot helper protocol with disposable engine slots."""
import os
from pathlib import Path
import sys
import threading
import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

TOOL_DIR = Path(__file__).resolve().parents[1] / "tools"
with patch.object(sys, "path", [str(TOOL_DIR), *sys.path]):
    import run_wishvale_start as handoff


@unittest.skipUnless(os.getenv("OT0_WISHVALE_REFERENCE"), "requires the private local reference")
class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        decoder = os.getenv("OT0_WISHVALE_DECODER")
        cls.world = handoff.start.unpack_save(Path(os.environ["OT0_WISHVALE_REFERENCE"]),
                                              Path(decoder) if decoder else None)
        donor = os.getenv("OT0_WISHVALE_CHARACTER")
        cls.character = handoff.start.unpack_save(Path(donor), Path(decoder) if decoder else None) if donor else cls.world

    def run_session(self, root, wrap, reject=False):
        bridge, slots = root / "bridge", root / "slots"
        slots.mkdir()
        manual = slots / "SaveData9.sav"
        manual.write_bytes(b"original")
        errors = []

        def serve():
            try:
                handoff.serve(self.world, [slots], bridge)
            except Exception as exc:
                errors.append(exc)

        def expect(path):
            end = time.monotonic() + 12
            while not path.is_file() and not errors and time.monotonic() < end:
                time.sleep(0.02)
            self.assertFalse(errors, str(errors))
            self.assertTrue(path.is_file(), str(path))

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        expect(bridge / "offer")
        token = (bridge / "offer").read_text().splitlines()[0]
        session = bridge / token
        def slot(kind):
            return slots / f"OT0AP_{token}_{kind}.sav"
        try:
            slot("probe").write_bytes(wrap(self.character))
            (session / "probe").touch()
            expect(session / "located")
            (session / "armed").touch()
            slot("character").write_bytes(wrap(self.character))
            (session / "donor").touch()
            expect(session / "ready")
            self.assertEqual(slot("wishvale").read_bytes(), wrap(handoff.start.build(
                self.world, self.character, outside_workshop=True)))
            if reject:
                (session / "stopped").write_text("engine rejected the staged slot")
            else:
                (session / "arrived").touch()
        finally:
            if not (session / "arrived").exists() and not (session / "stopped").exists():
                (session / "stopped").write_text("test ended")
            worker.join(12)
        self.assertFalse(worker.is_alive())
        self.assertEqual(bool(errors), reject)
        if reject:
            self.assertIn("engine rejected", (session / "error").read_text())
        self.assertEqual(manual.read_bytes(), b"original")
        self.assertEqual(list(slots.iterdir()), [manual])

    def test_raw_engine_roundtrip(self):
        with TemporaryDirectory() as temp:
            self.run_session(Path(temp), lambda raw: raw)

    def test_wrapped_slots_are_cleaned_after_game_rejects_load(self):
        with TemporaryDirectory() as temp:
            self.run_session(Path(temp), handoff.start.stored, reject=True)
