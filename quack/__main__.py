"""Quack CLI entry point.

Usage:
    quack                  → start interactive REPL (Кря shell)
    quack file.quack       → run a Quack source file
    quack -c "кряк('hi')"  → run a one-liner from the command line
    quack --version        → print version
    quack --help           → print this help
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import __version__
from .quack import run_quack


def _force_utf8_io() -> None:
    """Reconfigure stdout/stderr to UTF-8 on Windows (and elsewhere if cp*).

    Without this, `print('кряк')` raises UnicodeEncodeError when the console
    code page is cp1252 / cp866 / etc. — which is the default on Windows
    Python when the parent process didn't set PYTHONIOENCODING. Quack is
    Cyrillic-first, so a clean unicode stdout is non-negotiable.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            # Python 3.7+ — TextIOWrapper.reconfigure
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


HELP = """\
quack {ver} — Russian-English mixed programming language

Usage:
  quack                  start interactive REPL
  quack <file>           run a .quack source file
  quack -c "<code>"      run a one-liner from the command line
  quack -e <example>     run a bundled example (try: quack -e gpu_demo)
  quack --version        print version
  quack --help           print this help

Inside the REPL, type :help for available commands.
"""


def _run_source(src: str) -> int:
    """Run source through the full pipeline, print output, return exit code."""
    result = run_quack(src)
    out = result.get("output")
    if out:
        print(out)
    if not result.get("success"):
        err = result.get("error", "<unknown>")
        phase = result.get("phase", "?")
        print(f"quack: {phase} error: {err}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    _force_utf8_io()
    argv = sys.argv[1:]

    # No args → REPL
    if not argv:
        try:
            from .repl import main as repl_main
        except ImportError as e:  # pragma: no cover
            print(f"quack: cannot start REPL: {e}", file=sys.stderr)
            return 1
        return repl_main()

    arg = argv[0]

    if arg in ("--help", "-h"):
        print(HELP.format(ver=__version__))
        return 0

    if arg in ("--version", "-V"):
        print(f"quack {__version__}")
        return 0

    if arg in ("-c", "--code"):
        if len(argv) < 2:
            print("quack: -c requires a code string", file=sys.stderr)
            return 2
        return _run_source(argv[1])

    if arg in ("-e", "--example"):
        if len(argv) < 2:
            print("quack: -e requires an example name", file=sys.stderr)
            return 2
        from .quack import QUACK_EXAMPLES
        name = argv[1]
        if name not in QUACK_EXAMPLES:
            available = ", ".join(QUACK_EXAMPLES.keys())
            print(f"quack: unknown example '{name}'", file=sys.stderr)
            print(f"available: {available}", file=sys.stderr)
            return 2
        return _run_source(QUACK_EXAMPLES[name])

    # Otherwise treat as a file path
    src_path = Path(arg)
    if not src_path.exists():
        print(f"quack: file not found: {src_path}", file=sys.stderr)
        return 1
    if not src_path.is_file():
        print(f"quack: not a file: {src_path}", file=sys.stderr)
        return 1
    return _run_source(src_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
