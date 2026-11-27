"""Serve one native New Game handoff using the private, verified Wishvale reference."""
import argparse
import ctypes
import hashlib
import os
from pathlib import Path
import secrets
import sys
import time

import build_wishvale_start as start


def save_roots(extra):
    local = Path(os.environ["LOCALAPPDATA"])
    docs = Path.home() / "Documents"
    if os.name == "nt":
        path = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, path) == 0:
            docs = Path(path.value)
    return [*extra, local / "Octopath_Traveler0" / "Saved" / "SaveGames",
            docs / "My Games" / "Octopath_Traveler0" / "Steam"]


def wait_for(check, seconds, message):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = check()
        if value:
            return value
        time.sleep(0.2)
    raise TimeoutError(message)


def locate(roots, name):
    matches = set()
    for root in roots:
        if root.is_dir():
            matches.update(p.resolve() for p in root.rglob(name) if p.is_file())
    if len(matches) > 1:
        raise ValueError("Found the temporary slot in multiple locations")
    return next(iter(matches), None)


def publish(path, value):
    tmp = path.with_name(path.name + "." + secrets.token_hex(8) + ".tmp")
    try:
        tmp.write_text(value, encoding="ascii")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def serve(template, roots, bridge, decoder=None):
    if hashlib.sha256(template).hexdigest() != start.WORLD_SHA256:
        raise ValueError("Expected the verified pre-Stia world reference")
    bridge.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(16)
    prefix = "OT0AP_" + token
    session = bridge / token
    session.mkdir()
    offer = bridge / "offer"
    probe = donor = result = None
    # Only the current offer can be claimed. Older workers never consume a newer run.
    publish(offer, token + "\n" + str(int(time.time()) + 1800))
    def until(check, seconds, message):
        def active():
            if (session / "stopped").exists():
                raise ValueError("Mod stopped: " + (session / "stopped").read_text(errors="replace"))
            return check()
        return wait_for(active, seconds, message)

    try:
        print("Ready. Press Ctrl+Alt+W during New Game customization and wait here.", flush=True)
        until((session / "probe").exists, 1800, "Timed out waiting for the mod to arm")
        probe = until(lambda: locate(roots, prefix + "_probe.sav"), 12,
                      "Engine staging directory not found. Supply --save-root with the game's Saved directory.")
        # The probe is a completed native write. Its envelope determines the format
        # expected by the same engine API when it reads the finished character.
        with probe.open("rb") as stream:
            raw = stream.read(4) == b"GVAS"
        start.document(start.unpack_save(probe, decoder))
        publish(session / "located", "ok")
        until((session / "armed").exists, 30, "Opening event was not armed")
        print("Picker armed. Finish customization and confirm your primary job.", flush=True)
        until((session / "donor").exists, 1800, "Timed out waiting for job confirmation")
        donor = probe.with_name(prefix + "_character.sav")
        character = start.unpack_save(donor, decoder)
        candidate = start.build(template, character, outside_workshop=True)
        result_path = probe.with_name(prefix + "_wishvale.sav")
        with result_path.open("xb") as stream:
            result = result_path
            stream.write(candidate if raw else start.stored(candidate))
        publish(session / "ready", "ok")
        print("Wishvale character built. Waiting for the game to load the field.", flush=True)
        until((session / "arrived").exists, 120, "Timed out waiting for the Wishvale field")
        print("Wishvale loaded. Check your protagonist, Stia and the workshop in game.", flush=True)
    except (Exception, KeyboardInterrupt) as exc:
        publish(session / "error", str(exc).encode("ascii", "replace").decode("ascii") or "Cancelled")
        raise
    finally:
        # Keep the small session status for diagnostics. Only remove this session's
        # disposable slots. The unique offer expires even if the helper is closed.
        for item in (result, donor, probe):
            if item is not None:
                item.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=Path(__file__).with_name("Wishvale.gvas"))
    parser.add_argument("--decoder", type=Path)
    parser.add_argument("--save-root", type=Path, action="append", default=[])
    args = parser.parse_args()
    serve(start.unpack_save(args.template, args.decoder), save_roots(args.save_root),
          Path(os.environ["LOCALAPPDATA"]) / "OctopathArchipelagoBridge" / "WishvaleStart", args.decoder)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, AttributeError) as exc:
        sys.exit(f"Wishvale start stopped: {exc}")
