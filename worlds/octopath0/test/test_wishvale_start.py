"""Offline save-builder checks. Set OT0_WISHVALE_REFERENCE to exercise the private fixture."""
import copy
import os
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

TOOL_DIR = Path(__file__).resolve().parents[1] / "tools"
with patch.object(sys, "path", [str(TOOL_DIR), *sys.path]):
    import build_wishvale_start as start


class SaveFormatTests(unittest.TestCase):
    def test_literal_block_boundaries(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "slot.sav"
            for size in (1, start.BLOCK - 1, start.BLOCK, start.BLOCK + 1, 2 * start.BLOCK + 7):
                with self.subTest(size=size):
                    payload = bytes(range(253)) * (size // 253 + 1)
                    path.write_bytes(start.stored(payload[:size]))
                    self.assertEqual(start.unpack_save(path), payload[:size])

    def test_serialized_names(self):
        for name in ("Wren", "Étoile", "凛"):
            data = start.pack_string(name)
            self.assertEqual(start.fstring(data, 0), (name, len(data)))
        with self.assertRaises(ValueError):
            start.fstring(struct.pack("<i", 6) + b"short", 0)

    def test_unverified_world(self):
        with self.assertRaisesRegex(ValueError, "pre-Stia"):
            start.build(b"wrong world", b"")


@unittest.skipUnless(os.getenv("OT0_WISHVALE_REFERENCE"), "requires the private local reference")
class WishvaleStartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        decoder = os.getenv("OT0_WISHVALE_DECODER")
        cls.world = start.unpack_save(Path(os.environ["OT0_WISHVALE_REFERENCE"]),
                                      Path(decoder) if decoder else None)

    def test_reference_candidate(self):
        prefix, baseline = start.document(self.world)
        after_prefix, after = start.document(start.build(self.world, self.world, "Wren"))
        self.assertEqual(prefix, after_prefix)
        changed = {k for k in after if baseline[k] != after[k]}
        self.assertEqual(changed, {"SaveDataPC", "SaveDataPCSkillBoard", "SaveNames"})
        pcs = start.records(after["SaveDataPC"], "PCMsdID")
        boards = start.records(after["SaveDataPCSkillBoard"], "PCMsdID")
        for ident in (start.HERO, start.STIA):
            self.assertEqual([start.integer(pcs[ident][k]) for k in ("Exp", "NowLv", "NowHp", "NowSp")],
                             [0, 1, 1, 0])
            self.assertEqual(start.integer(boards[ident]["NowJp"]), 0)
        names = start.fields(after["SaveNames"])
        self.assertEqual(start.fstring(names["MainCharacterName"].value, 0)[0], "Wren")

    def test_other_job_donor_and_binding_guard(self):
        prefix, donor = start.document(self.world)
        avatar = start.fields(donor["SaveDataMainCharacter"])
        start.set_int(avatar, "JobID", 1)
        start.set_int(avatar, "ReleasedJob", 2)
        donor["SaveDataMainCharacter"].value = start.encode_tags(avatar)
        equip = start.records(donor["SaveDataPCSetEquip"], "PCMsdID")
        gear = start.int_list(equip[901]["EquipWeaponMsdID"])
        bag = start.records(donor["SaveDataItem"], "ItemMsdID")
        for ident in gear:
            row = copy.deepcopy(bag[50290])
            start.set_int(row, "ItemMsdID", ident)
            start.set_int(row, "Num", 1)
            bag[ident] = row
        # Stia's armor and building materials must survive even if the donor lacks them.
        del bag[120000], bag[130069], bag[103001]
        donor["SaveDataItem"].value = start.encode_rows(bag)
        raw = prefix + start.encode_tags(donor) + bytes(4)
        _, candidate = start.document(start.build(self.world, raw))
        self.assertEqual(candidate["SaveDataMainCharacter"], donor["SaveDataMainCharacter"])
        merged = start.records(candidate["SaveDataItem"], "ItemMsdID")
        self.assertTrue(set(gear) <= merged.keys())
        # Only Stia uses this weapon with this job, despite two copies in the template.
        self.assertEqual(start.integer(merged[103001]["Num"]), 1)
        self.assertEqual(start.integer(merged[120000]["Num"]), 1)
        self.assertEqual(start.integer(merged[130069]["Num"]), 4)
        variables = start.records(donor["SaveDataGameVariable"], "GameVariableMtdID")
        marker = copy.deepcopy(next(iter(variables.values())))
        start.set_int(marker, "GameVariableMtdID", 900000100)
        variables[900000100] = marker
        donor["SaveDataGameVariable"].value = start.encode_rows(variables)
        with self.assertRaisesRegex(ValueError, "unbound"):
            start.build(self.world, prefix + start.encode_tags(donor) + bytes(4))

    def test_existing_slot_survives_cli(self):
        with TemporaryDirectory() as directory:
            template = Path(directory) / "template.gvas"
            output = Path(directory) / "existing.sav"
            template.write_bytes(self.world)
            output.write_bytes(b"keep my slot")
            with patch.object(sys, "argv", ["build_wishvale_start", str(template), str(output)]):
                with self.assertRaises(FileExistsError):
                    start.main()
            self.assertEqual(output.read_bytes(), b"keep my slot")


if __name__ == "__main__":
    unittest.main()
