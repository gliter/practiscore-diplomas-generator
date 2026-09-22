import sys
import traceback

from practiscore_diplomas.cli import main


def _wait_for_key() -> None:
    if not sys.stdin or not sys.stdin.isatty():
        return
    print("\nPress any key to close...", end="", flush=True)
    try:
        import msvcrt

        msvcrt.getch()
    except ImportError:
        input()


def run() -> int:
    try:
        return main()
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
        if exit_code != 0:
            _wait_for_key()
        return exit_code
    except BaseException:
        traceback.print_exc()
        _wait_for_key()
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
