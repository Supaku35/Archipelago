import argparse
from save_binding import request_save_binding

def main(argv=None):
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--initialize", action="store_true")
    modes.add_argument("--inspect", action="store_true")
    modes.add_argument("--authorize", action="store_true")
    modes.add_argument("--test-mismatch", action="store_true")
    args = parser.parse_args(argv)

    operation = (
        "authorize" if args.authorize
        else "initialize" if args.initialize
        else "inspect"
    )
    return request_save_binding(
        operation,
        test_mismatch=args.test_mismatch,
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped. Do not authorize the old inbox request.")
    except Exception as exc:
        raise SystemExit(f"Live binding error: {exc}")