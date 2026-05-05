"""`python -m quack <file.quack>` — run a Quack source file."""

import sys
from pathlib import Path
from .quack import run_quack


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m quack <file.quack>", file=sys.stderr)
        return 2
    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"quack: file not found: {src_path}", file=sys.stderr)
        return 1
    src = src_path.read_text(encoding="utf-8")
    run_quack(src)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
