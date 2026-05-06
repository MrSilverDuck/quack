"""
Quack — the Russian-English mixed programming language.

🦆 Кря! Welcome to Quack — a programming language with 364 keywords across
9 natural languages (Russian, English, Ukrainian, Spanish, Chinese, etc.),
zoomer-mode slang, and a built-in teacher system.

Built by Nightbox LLC. MIT licensed. Part of the SilverDuck ecosystem.

Quick start:
    >>> from quack import run_quack
    >>> result = run_quack("кряк('Привет, мир!')")
    >>> print(result["output"])

From the CLI:
    $ quack                    # interactive REPL
    $ quack file.quack         # run a script
    $ quack -c "кряк('hi')"    # run a one-liner
    $ quack -e gpu_demo        # run a bundled example
"""

from .quack import run_quack, KEYWORDS, TRUTHY_WORDS, QUACK_EXAMPLES  # noqa: F401

__version__ = "0.2.0"
__author__ = "Nightbox LLC"
__license__ = "MIT"

__all__ = [
    "run_quack",
    "KEYWORDS",
    "TRUTHY_WORDS",
    "QUACK_EXAMPLES",
    "__version__",
]
