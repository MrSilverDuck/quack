"""Stub for QuackKeystone — the real implementation lives in Nightbox-internal
distribution and requires a Keystone 3 Pro hardware wallet.

This stub keeps the public Quack interpreter import-safe: the symbol exists,
but instantiating it raises a clear error.
"""


class QuackKeystone:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "QuackKeystone requires a Keystone 3 Pro hardware wallet and the "
            "Nightbox-internal `quack_keystone` module. It is not part of the "
            "public Quack distribution. The rest of Quack works without it."
        )
