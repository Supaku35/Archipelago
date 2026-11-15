import asyncio

from save_binding import request_save_binding
from ap_connection import SEED, expect
from ap_history import read_verified_history, plan_pending


def main():
    history = asyncio.run(read_verified_history())

    # Reuses the verified server identity and read-only Lua request.
    binding = request_save_binding("inspect")
    if binding is None:
        raise RuntimeError(
            "This save has no live binding. Initialize it separately first."
        )

    expect("Reconciliation seed", binding["seed"], SEED)
    expect("Reconciliation team", binding["team"], 0)
    expect("Reconciliation slot", binding["slot"], 1)
    next_index = binding["next_index"]
    pending = plan_pending(history, next_index)

    print("\nREAD-ONLY RECONCILIATION")
    print(f"Verified AP history length: {len(history)}")
    print(f"Saved live next delivery index: {next_index}")
    print(f"Pending deliveries: {len(pending)}")

    for index, item in pending:
        print(
            f"PENDING index {index}: AP item {item['item']} -> "
            "Small Shield, game item 110001, quantity 1."
        )
        print(
            f"  Source location={item['location']}, "
            f"player={item['player']}, flags={item['flags']}"
        )

    if not pending:
        print("Caught up according to the loaded save's live counter.")

    print("No delivery requests published; no items granted or progress changed.")
    print("No location checks or goal submitted.")
    print(
        "Comparison of in-memory snapshots only; "
        "this does not authorize delivery or prove a disk save."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Reconciliation cancelled. Do not authorize the old inbox request.")
    except TimeoutError:
        raise SystemExit("Reconciliation timed out. No automatic retry.")
    except Exception as exc:
        raise SystemExit(f"Reconciliation failed: {type(exc).__name__}: {exc}")
