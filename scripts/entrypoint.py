import ctypes
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


def _attach_console_for_cli() -> None:
    """Restore streams for CLI use in a windowed PyInstaller build."""
    if sys.stdout is not None and sys.stderr is not None or sys.platform != "win32":
        return
    kernel = ctypes.windll.kernel32
    if not kernel.AttachConsole(-1):
        kernel.AllocConsole()
    sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    sys.__stdin__, sys.__stdout__, sys.__stderr__ = sys.stdin, sys.stdout, sys.stderr


def run() -> int:
    try:
        if sys.argv[1:]:
            _attach_console_for_cli()
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
