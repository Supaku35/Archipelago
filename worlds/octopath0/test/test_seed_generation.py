"""Exercise the player YAMLs through Generate.py and read the final server archives."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import zlib

from Utils import restricted_loads


WORLD = Path(__file__).resolve().parents[1]
CAVERN = ("Cerulean Caverns - Southwest Cliff Chest", 10070117, 70117)
TRAIL = ("Wishvale Trail - West Stump Chest", 10070115, 70115)


class SeedGenerationTests(unittest.TestCase):
    def test_live_sender_matches_shipped_seed(self):
        # This fixture stays pinned when the generator's catalog evolves.
        with patch.object(sys, "path", [str(WORLD / "PythonSender"), *sys.path]):
            import submit_two_chest as sender

        for seed, expected_slot, digest in sender.PROFILES.values():
            with self.subTest(seed=seed), zipfile.ZipFile(WORLD / "test" / f"AP_{seed}.zip") as archive:
                data = restricted_loads(zlib.decompress(archive.read(f"AP_{seed}.archipelago")[1:]))
                self.assertEqual(data["seed_name"], seed)
                self.assertEqual(data["slot_info"][1].name, sender.PLAYER)
                self.assertEqual(json.loads(json.dumps(data["slot_data"][1])), expected_slot)
                self.assertEqual(set(data["locations"][1]), set(sender.location_map(expected_slot).values()))
                if digest:
                    catalog = data["datapackage"]["Octopath Traveler 0"]["location_name_to_id"]
                    self.assertEqual(len(catalog), 168)
                    serialized = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
                    self.assertEqual(hashlib.sha256(serialized).hexdigest(), digest)

    def test_player_presets(self):
        for player, rows, schema, goal in [
            ("OT0Prototype", [CAVERN], 1, "receive_small_shield"),
            ("OT0TwoChest", [CAVERN, TRAIL], 2, "receive_two_small_shields"),
        ]:
            with self.subTest(player=player), tempfile.TemporaryDirectory() as output:
                subprocess.run([
                    sys.executable, "Generate.py", "--seed", "70115",
                    "--player_files_path", str(WORLD / f"Players_{player}"),
                    "--outputpath", output, "--spoiler", "0",
                ], check=True, cwd=WORLD.parents[1],
                    env={**os.environ, "SKIP_REQUIREMENTS_UPDATE": "1"})
                archive, = Path(output).glob("*.zip")
                with zipfile.ZipFile(archive) as seed:
                    datafile, = [p for p in seed.namelist() if p.endswith(".archipelago")]
                    data = restricted_loads(zlib.decompress(seed.read(datafile)[1:]))
                self.assertEqual(data["slot_info"][1].name, player)
                self.assertEqual(data["locations"], {
                    1: {ap_id: (10110001, 1, 1) for _, ap_id, _ in rows}
                })
                self.assertEqual(data["slot_data"][1], {
                    "prototype_schema": schema,
                    "prototype_goal": goal,
                    "locations": tuple({"name": n, "ap_location_id": a, "game_treasure_id": t}
                                       for n, a, t in rows),
                    "items": ({"name": "Small Shield", "ap_item_id": 10110001,
                               "game_item_id": 110001, "quantity": 1},),
                })
