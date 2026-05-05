"""
Quack — the Russian-English mixed programming language.

🦆 Кря! Welcome to Quack — a programming language with 364 keywords across
9 natural languages (Russian, English, Ukrainian, Spanish, Chinese, etc.),
zoomer-mode slang, and a built-in teacher system.

Built by Nightbox LLC. MIT licensed. Part of the SilverDuck ecosystem.

Quick start:
    >>> from quack import run_quack
    >>> run_quack("кря; сказать 'Привет, мир!'")

Or from the CLI:
    $ python -m quack examples/sample.quack
"""

from .quack import run_quack, KEYWORDS, TRUTHY_WORDS  # noqa: F401

__version__ = "0.1.1-beta.1"
__author__ = "Nightbox LLC"
__license__ = "MIT"
