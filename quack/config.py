"""Quack configuration — auto-detects optional UniGPU runtime.

The Quack interpreter runs purely on Python, but if `unigpu_ffi.dll`
(from https://github.com/MrSilverDuck/unigpu) is on the system, Quack
will use it for GPU-accelerated kernels. Otherwise it falls back to
pure-Python evaluation.
"""

import os
from pathlib import Path

# Where to look for `unigpu_ffi.dll` / `libunigpu_ffi.so` (in priority order).
# Override with $QUACK_UNIGPU_ROOT or $UNIGPU_ROOT.
def _find_unigpu_root() -> Path:
    env = os.environ.get("QUACK_UNIGPU_ROOT") or os.environ.get("UNIGPU_ROOT")
    if env:
        return Path(env)
    # If quack is installed via pip alongside a built unigpu repo, it
    # may sit at ../unigpu/ relative to this file.
    here = Path(__file__).resolve().parent.parent
    sibling = here.parent / "unigpu"
    if sibling.exists():
        return sibling
    # Last resort — return a pseudo path; quack falls back to pure-Python.
    return here


UNIGPU_ROOT: Path = _find_unigpu_root()
