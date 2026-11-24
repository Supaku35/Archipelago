import os
import re
import tempfile
import time
from pathlib import Path

class BridgeCancelled(RuntimeError):
    """The bridge confirmed cancellation of this request's staged batch."""


def publish(path, text):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def read_response(folder, request_id):
    path = folder / f"{request_id}.response"

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        # The mod may briefly remove the old response while replacing it.
        return None

    if (
        len(lines) != 7
        or lines[0] != "OT0AP_RESPONSE_V1"
        or lines[1] != request_id
        or lines[6] != "END"
        or lines[2] not in {
            "staged", "deferred", "processed", "gap", "blocked", "progress",
            "cancelled"
        }
    ):
        raise RuntimeError("Invalid response; stopping without retry.")

    return {
        "status": lines[2],
        "next_index": lines[3],
        "save": lines[4],
        "detail": lines[5],
    }


def wait_for_bridge_response(
    folder, request_id, terminal_status, timeout, expected_save=None
):
    deadline = time.monotonic() + timeout
    previous_status = None
    observed_save = expected_save

    while True:
        inbox_lines = (folder / "inbox.txt").read_text(
            encoding="utf-8"
        ).splitlines()

        if (
            len(inbox_lines) < 2
            or inbox_lines[0] not in {
                "OT0AP_TEST_V3", "OT0AP_QUERY_V1", "OT0AP_LIVE_V1", "OT0AP_BOUND_ITEM_V1"
            }
            or inbox_lines[1] != request_id
        ):
            raise RuntimeError(
                "Inbox was replaced by another request. Stopping."
            )

        response = read_response(folder, request_id)

        if response is not None:
            status = response["status"]

            if status != previous_status:
                print(
                    f"Response: {status}; "
                    f"next index={response['next_index']}",
                    flush=True,
                )
                print(response["detail"], flush=True)
                previous_status = status

            if status == "cancelled":
                raise BridgeCancelled(
                    "Bridge was disarmed and the staged batch was cancelled. "
                    "No further requests sent. Start a new coordinator "
                    "and authorize its query when ready."
                )

            if status in {"blocked", "gap"}:
                raise RuntimeError(
                    f"Bridge returned '{status}'. "
                    "No further requests sent; inspect before retrying."
                )

            allowed = {terminal_status}
            if terminal_status == "processed":
                allowed.update({"staged", "deferred"})

            if status not in allowed:
                raise RuntimeError("Unexpected response type for this request.")

            save_name = response["save"]
            if save_name in {"", "unknown", "nil"}:
                raise RuntimeError("Response lacks a usable save identity.")

            if observed_save is None:
                observed_save = save_name
            elif save_name != observed_save:
                raise RuntimeError(
                    "Observed save object changed during this run. Stopping."
                )

            if status == terminal_status:
                raw_index = response["next_index"]
                if not re.fullmatch(r"\d{1,7}", raw_index):
                    raise RuntimeError("Invalid progress counter.")

                next_index = int(raw_index)
                if next_index > 1_000_000:
                    raise RuntimeError("Progress exceeds the prototype limit.")

                return next_index, observed_save

        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Timed out waiting for {request_id}. "
                "No automatic retry. A request may remain in the game. "
                "Press Ctrl+F3 in-game to disarm pending delivery."
            )

        time.sleep(0.5)

