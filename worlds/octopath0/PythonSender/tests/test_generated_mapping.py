import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generated_room import GeneratedRoom
from two_chest_profiles import REVISED_SLOT_DATA


class GeneratedMappingTests(unittest.TestCase):
    def setUp(self):
        self.room = GeneratedRoom("01234", "OT0TwoChest")
        self.slot = copy.deepcopy(REVISED_SLOT_DATA)
        # AP IDs are supplied by the generated room. The game IDs stay stable.
        for i, row in enumerate(self.slot["locations"]):
            row["ap_location_id"] = 40000 + i
        self.slot["items"][0]["ap_item_id"] = 90000
        self.package = {
            "location_name_to_id": {r["name"]: r["ap_location_id"] for r in self.slot["locations"]},
            "item_name_to_id": {"Small Shield": 90000},
        }

    def test_room_mappings_and_conflicting_package(self):
        self.room.validate_slot(self.slot, self.package)
        self.package["item_name_to_id"]["Small Shield"] = 90001
        with self.assertRaises(RuntimeError):
            self.room.validate_slot(self.slot, self.package)

    def test_reject_unsupported_schema_unsafe_grants_and_swapped_treasures(self):
        for key, value in (("prototype_schema", True), ("prototype_schema", 3),
                           ("prototype_goal", "other")):
            with self.assertRaises(RuntimeError):
                self.room.validate_slot(dict(self.slot, **{key: value}), self.package)
        for key, value in (("game_item_id", 110000), ("quantity", True), ("quantity", 2)):
            slot = copy.deepcopy(self.slot)
            slot["items"][0][key] = value
            with self.assertRaises(RuntimeError):
                self.room.validate_slot(slot, self.package)
        self.slot["locations"][0]["game_treasure_id"] = 70115
        with self.assertRaises(RuntimeError):
            self.room.validate_slot(self.slot, self.package)
