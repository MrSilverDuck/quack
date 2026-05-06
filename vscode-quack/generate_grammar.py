"""
Generate the VS Code TextMate grammar (syntaxes/quack.tmLanguage.json)
straight from quack/quack.py:KEYWORDS so the grammar can never drift
from the interpreter.

Run after touching KEYWORDS:
    python vscode-quack/generate_grammar.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Add quack-repo to sys.path so we can import the live interpreter dicts.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from quack.quack import KEYWORDS, TRUTHY_WORDS  # noqa: E402


# Bucket keywords by their TokenType value (which is the string-role).
def bucket(*roles: str) -> list[str]:
    return sorted({k for k, v in KEYWORDS.items() if v in roles})


CONTROL    = bucket("IF", "ELSE", "WHILE", "FOR", "IN", "BREAK", "CONTINUE", "RETURN")
DECL       = bucket("LET", "FN", "IMPORT")
IO         = bucket("PRINT")
LOGIC      = bucket("AND", "OR", "NOT")
CONSTANTS  = sorted(set(bucket("BOOL", "NULL")) | set(TRUTHY_WORDS))
NAMESPACES = bucket("GPU")


def alt(words: list[str]) -> str:
    """Produce a regex alternation that matches any of the words.

    TextMate uses Oniguruma; \\b doesn't always work for Cyrillic boundaries,
    so we emulate \\b with negative lookarounds on `\\w`.
    """
    # Sort longest first so e.g. `крякнуть` matches before `кря`
    words = sorted(set(words), key=lambda w: (-len(w), w))
    escaped = [re.escape(w) for w in words]
    return r"(?<![\w])(" + "|".join(escaped) + r")(?![\w])"


grammar = {
    "$schema": "https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json",
    "name": "Quack",
    "scopeName": "source.quack",
    "fileTypes": ["quack", "kry", "кря"],
    "patterns": [
        {"include": "#comments"},
        {"include": "#strings"},
        {"include": "#numbers"},
        {"include": "#keywords"},
        {"include": "#operators"},
    ],
    "repository": {
        "comments": {
            "patterns": [
                {"name": "comment.line.number-sign.quack",  "match": r"#.*$"},
                {"name": "comment.line.double-slash.quack", "match": r"//.*$"},
            ]
        },
        "strings": {
            "patterns": [
                {
                    "name": "string.quoted.double.quack",
                    "begin": r'"',
                    "end":   r'"',
                    "patterns": [
                        {"name": "constant.character.escape.quack", "match": r"\\."}
                    ],
                },
                {
                    "name": "string.quoted.single.quack",
                    "begin": r"'",
                    "end":   r"'",
                    "patterns": [
                        {"name": "constant.character.escape.quack", "match": r"\\."}
                    ],
                },
            ]
        },
        "numbers": {
            "patterns": [
                {"name": "constant.numeric.float.quack",   "match": r"\b\d+\.\d+\b"},
                {"name": "constant.numeric.integer.quack", "match": r"\b\d+\b"},
            ]
        },
        "keywords": {
            "patterns": [
                {"name": "keyword.control.quack",          "match": alt(CONTROL)},
                {"name": "storage.type.quack",             "match": alt(DECL)},
                {"name": "support.function.builtin.quack", "match": alt(IO)},
                {"name": "keyword.operator.logical.quack", "match": alt(LOGIC)},
                {"name": "constant.language.quack",        "match": alt(CONSTANTS)},
                {"name": "support.class.quack",            "match": alt(NAMESPACES)},
            ]
        },
        "operators": {
            "patterns": [
                {"name": "keyword.operator.comparison.quack", "match": r"==|!=|<=|>=|<|>"},
                {"name": "keyword.operator.assignment.quack", "match": r"="},
                {"name": "keyword.operator.arithmetic.quack", "match": r"\+|-|\*|/|%"},
            ]
        },
    },
}


out = ROOT / "vscode-quack" / "syntaxes" / "quack.tmLanguage.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(grammar, indent=2, ensure_ascii=False), encoding="utf-8")

# Stats
n_total = sum(len(b) for b in (CONTROL, DECL, IO, LOGIC, CONSTANTS, NAMESPACES))
print(f"wrote {out.relative_to(ROOT)}")
print(f"  control:    {len(CONTROL):4} keywords")
print(f"  decl:       {len(DECL):4} keywords")
print(f"  io:         {len(IO):4} keywords")
print(f"  logic:      {len(LOGIC):4} keywords")
print(f"  constants:  {len(CONSTANTS):4} keywords")
print(f"  namespaces: {len(NAMESPACES):4} keywords")
print(f"  --------------------")
print(f"  total:      {n_total:4} keywords highlighted")
