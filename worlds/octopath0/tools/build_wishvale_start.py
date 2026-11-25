"""Build an offline pre-Stia Wishvale test slot from the recorded world and a starter character."""
import argparse
from collections import Counter
import ctypes
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct

# Hash of the decoded, observed BeforeStia world. Personal save bytes stay local.
WORLD_SHA256 = "941f6818df0cb81edc3f41c44198c87c066fde0c8c7ff3f63e1c5214d0283ddc"
MAX_SIZE = 64 * 1024 * 1024
BLOCK = 0x40000
HERO = 900
STIA = 40204
HERO_ROWS = set(range(900, 910))
CHARACTER_TABLES = ("SaveDataPCSetEquip", "SaveDataPCSetSkill", "SaveDataPCSkillBoard")
WORLD_SUPPLIES = (50290, 130069, 130096, 130098)  # Ring, lumber, stone, cloth


def require(condition, message):
    if not condition:
        raise ValueError(message)


def i32(data, pos=0):
    require(0 <= pos <= len(data) - 4, "Truncated integer")
    return struct.unpack_from("<i", data, pos)[0]


def fstring(data, pos):
    size = i32(data, pos)
    start = pos + 4
    unit = 2 if size < 0 else 1
    end = start + abs(size) * unit
    require(end <= len(data) and abs(size) <= 65536, "Invalid string length")
    if not size:
        return "", end
    require(data[end-unit:end] == bytes(unit), "Unterminated string")
    return data[start:end-unit].decode("utf-16-le" if size < 0 else "utf-8"), end


def pack_string(value):
    if value.isascii():
        return struct.pack("<i", len(value) + 1) + value.encode() + b"\0"
    data = value.encode("utf-16-le") + b"\0\0"
    return struct.pack("<i", -(len(data) // 2)) + data


def read_type(data, pos, depth=0):
    require(depth <= 8, "Invalid type nesting")
    kind, pos = fstring(data, pos)
    count = i32(data, pos)
    require(0 <= count <= 8, "Invalid type count")
    pos += 4
    for _ in range(count):
        _, pos = read_type(data, pos, depth + 1)
    return kind, pos


@dataclass
class Tag:
    kind: str
    header: bytes
    flag: int
    value: bytes

    def encode(self):
        return self.header + struct.pack("<iB", len(self.value), self.flag) + self.value


END = pack_string("None")


def read_tags(data, pos=0):
    tags = {}
    while True:
        start = pos
        name, pos = fstring(data, pos)
        if name == "None":
            return tags, pos
        require(name and name not in tags, "Duplicate or missing property name")
        kind, pos = read_type(data, pos)
        header = data[start:pos]
        size = i32(data, pos)
        require(size >= 0 and pos + 5 + size <= len(data), "Invalid property size")
        flag = data[pos+4]
        require(flag in (0, 8, 16), "Unsupported property flags")
        pos += 5
        tags[name] = Tag(kind, header, flag, data[pos:pos+size])
        pos += size


def encode_tags(tags):
    return b"".join(tag.encode() for tag in tags.values()) + END


def document(data):
    marker = pack_string("/Script/Kingship.QPSaveData") + b"\0"
    pos = data.find(marker, 0, 65536)
    require(data.startswith(b"GVAS") and pos >= 0, "Expected a Kingship QPSaveData file")
    pos += len(marker)
    tags, end = read_tags(data, pos)
    require(data[end:] == bytes(4), "Unexpected save trailer")
    return data[:pos], tags


def fields(tag):
    require(tag.kind == "StructProperty", "Expected structure")
    tags, end = read_tags(tag.value)
    require(end == len(tag.value), "Unexpected structure trailer")
    return tags


def records(tag, key):
    require(tag.kind == "ArrayProperty", "Expected record array")
    count = i32(tag.value)
    require(0 <= count <= 100000, "Invalid row count")
    rows = {}
    pos = 4
    for _ in range(count):
        row, pos = read_tags(tag.value, pos)
        ident = integer(row[key])
        require(ident not in rows, f"Duplicate {key} {ident}")
        rows[ident] = row
    require(pos == len(tag.value), "Unexpected array trailer")
    return rows


def encode_rows(rows):
    return struct.pack("<i", len(rows)) + b"".join(encode_tags(row) for row in rows.values())


def integer(tag):
    require(tag.kind == "IntProperty" and len(tag.value) == 4, "Expected integer property")
    return i32(tag.value)


def set_int(row, name, value):
    integer(row[name])
    row[name].value = struct.pack("<i", value)


def int_list(tag):
    n = i32(tag.value)
    require(tag.kind == "ArrayProperty" and 0 <= n <= 1024 and len(tag.value) == 4 + n*4,
            "Invalid equipment list")
    return struct.unpack_from(f"<{n}i", tag.value, 4)


def stored(data):
    # Independent, literal Kraken blocks. Standard framing avoids an encoder dependency.
    return struct.pack("<Q", len(data)) + b"".join(
        b"\xcc\x06" + data[i:i+BLOCK] for i in range(0, len(data), BLOCK))


def unpack_save(path, decoder=None):
    require(0 < path.stat().st_size <= MAX_SIZE + 1024, "Unsupported input size")
    data = path.read_bytes()
    if data.startswith(b"GVAS"):
        return data
    require(len(data) > 10, "Truncated save")
    size, = struct.unpack_from("<Q", data)
    require(0 < size <= MAX_SIZE, "Unsupported decoded size")
    if len(data) == 8 + size + 2*((size + BLOCK - 1)//BLOCK):
        chunks = []
        for off in range(8, len(data), BLOCK + 2):
            if data[off:off+2] != b"\xcc\x06":
                break
            chunks.append(data[off+2:off+2+BLOCK])
        else:
            return b"".join(chunks)
    require(decoder is not None, "Compressed input requires --decoder with a trusted local Oodle or libooz library")
    lib = ctypes.CDLL(str(decoder.resolve(strict=True)))
    source = ctypes.create_string_buffer(data[8:] + bytes(64))
    target = ctypes.create_string_buffer(size + 64)
    if hasattr(lib, "OodleLZ_Decompress"):
        fn = lib.OodleLZ_Decompress
        ptr, length, flag = ctypes.c_void_p, ctypes.c_ssize_t, ctypes.c_int
        fn.argtypes = [ptr, length, ptr, length, flag, flag, flag, ptr, length, ptr, ptr, ptr, length, flag]
        fn.restype = length
        result = fn(source, len(data)-8, target, size, 1, 0, 0, None, 0, None, None, None, 0, 3)
    else:
        fn = lib.Kraken_Decompress
        fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
        fn.restype = ctypes.c_int
        result = fn(source, len(data)-8, target, size)
    require(result == size and target.raw[:4] == b"GVAS", "Decompression failed")
    return target.raw[:size]


def build(template, character, name=None):
    require(hashlib.sha256(template).hexdigest() == WORLD_SHA256,
            "World template must be the verified pre-Stia reference")
    prefix, world = document(template)
    _, donor = document(character)
    avatar = fields(donor["SaveDataMainCharacter"])
    job = integer(avatar["JobID"])
    require(integer(avatar["Created"]) == 1 and 1 <= job <= 8, "Choose a character with its primary job selected")
    require(integer(avatar["ReleasedJob"]) == 1 << job, "Choose an early character with only the starting job unlocked")
    donor_pcs = records(donor["SaveDataPC"], "PCMsdID")
    require(1 <= integer(donor_pcs[HERO]["NowLv"]) <= 6, "Choose an early character at LV1–6")
    donor_variables = records(donor["SaveDataGameVariable"], "GameVariableMtdID")
    require(not any(900000100 <= k <= 900000169 for k in donor_variables), "Choose an unbound character save")

    world["SaveDataMainCharacter"].value = donor["SaveDataMainCharacter"].value
    names = fields(donor["SaveNames"])
    if name is not None:
        require(1 <= len(name) <= 8 and all(c.isprintable() for c in name), "Use a name of 1–8 printable characters")
        require(names["MainCharacterName"].kind == "StrProperty", "Unknown name field")
        names["MainCharacterName"].value = pack_string(name)
    world["SaveNames"].value = encode_tags(names)
    user, origin = fields(world["SaveDataUser"]), fields(donor["SaveDataUser"])
    for key in ("PlayerNameLanguage", "FavoriteDishLanguage"):
        set_int(user, key, integer(origin[key]))
    world["SaveDataUser"].value = encode_tags(user)

    pcs = records(world["SaveDataPC"], "PCMsdID")
    # Start with low current HP/SP so the workshop can establish native full values.
    for ident in (HERO, STIA):
        for key, value in (("NowLv", 1), ("Exp", 0), ("NowHp", 1), ("NowSp", 0)):
            set_int(pcs[ident], key, value)
    world["SaveDataPC"].value = encode_rows(pcs)

    required_gear = Counter()
    for key in CHARACTER_TABLES:
        local = records(world[key], "PCMsdID")
        source = records(donor[key], "PCMsdID")
        require(HERO_ROWS <= local.keys() and HERO_ROWS <= source.keys(), "Incomplete protagonist job records")
        for ident in HERO_ROWS:
            local[ident] = source[ident]
        if key == "SaveDataPCSkillBoard":
            for ident in (*HERO_ROWS, STIA):
                set_int(local[ident], "NowJp", 0)
        if key == "SaveDataPCSetEquip":
            for ident in (900 + job, STIA):
                for field in ("EquipWeaponMsdID", "EquipArmorMsdID", "EquipAccessoryMsdID", "EquipRuneMsdID"):
                    required_gear.update(i for i in int_list(local[ident][field]) if i > 0)
        world[key].value = encode_rows(local)

    # Keep native starter choices (including food/masteries) from the donor.
    # Supply the known post-workshop materials, ring and Stia's worn equipment.
    stock = records(world["SaveDataItem"], "ItemMsdID")
    bag = records(donor["SaveDataItem"], "ItemMsdID")
    for ident in WORLD_SUPPLIES:
        bag[ident] = stock[ident]
    for ident, minimum in required_gear.items():
        if ident not in bag:
            require(ident in stock, f"Missing equipped item record {ident}")
            bag[ident] = stock[ident]
        if integer(bag[ident]["Num"]) < minimum:
            set_int(bag[ident], "Num", minimum)
    world["SaveDataItem"].value = encode_rows(bag)
    return prefix + encode_tags(world) + bytes(4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--character", type=Path, help="An early unbound save with a chosen job")
    parser.add_argument("--name", help="Optional test-slot display name")
    parser.add_argument("--decoder", type=Path, help="Trusted local native decoder for compressed input")
    args = parser.parse_args()
    template = unpack_save(args.template, args.decoder)
    character = unpack_save(args.character, args.decoder) if args.character else template
    candidate = stored(build(template, character, args.name))
    # Exclusive creation also protects inputs and pre-existing slots.
    with args.output.open("xb") as output:
        try:
            output.write(candidate)
        except BaseException:
            output.close()
            args.output.unlink()
            raise
    print(f"Created {args.output} ({len(candidate)} bytes).")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, AttributeError) as exc:
        raise SystemExit(f"Candidate build stopped: {exc}")
