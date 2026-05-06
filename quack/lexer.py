"""
Pygments lexer for the Quack / КРЯКА programming language.

Registered as an entry point under [project.entry-points."pygments.lexers"]
so any Pygments-using tool (Sphinx, Jupyter, Pelican, mkdocs-material…)
will syntax-highlight ```quack code blocks automatically.

The lexer is also consumed by the interactive REPL (`quack/repl.py`) via
`prompt_toolkit.lexers.PygmentsLexer` to colorize input as you type.

Usage from Pygments:
    >>> from pygments import highlight
    >>> from pygments.formatters import TerminalFormatter
    >>> from quack.lexer import QuackLexer
    >>> highlight("кряк('hi')", QuackLexer(), TerminalFormatter())
"""
from __future__ import annotations

from pygments.lexer import RegexLexer, words, include
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
)

# Pull keyword sets directly from the interpreter so they can never drift.
from .quack import KEYWORDS, TRUTHY_WORDS

# Group keywords by token-type role so we can color them differently.
# TokenType values are plain strings (TokenType.LET == "LET"), so we bucket by
# the value itself rather than by an `.name` attribute (which doesn't exist).
_TOK: dict[str, list[str]] = {}
for kw, tt in KEYWORDS.items():
    role = tt if isinstance(tt, str) else getattr(tt, "name", str(tt))
    _TOK.setdefault(role, []).append(kw)


def _kw(role: str) -> tuple[str, ...]:
    """Return the sorted keyword tuple for a given TokenType role."""
    return tuple(sorted(_TOK.get(role, [])))


# Coarse buckets for highlighting:
#   control flow:  IF/ELSE/WHILE/FOR/IN/BREAK/CONTINUE/RETURN
#   declaration:   LET/FN/IMPORT
#   I/O:           PRINT
#   logical:       AND/OR/NOT
#   constants:     BOOL/NULL  (also TRUTHY_WORDS)
#   namespace:     GPU
_CONTROL = sum(
    (_kw(r) for r in (
        "IF", "ELSE", "WHILE", "FOR", "IN", "BREAK", "CONTINUE", "RETURN",
    )),
    (),
)
_DECL = sum((_kw(r) for r in ("LET", "FN", "IMPORT")), ())
_IO = _kw("PRINT")
_LOGIC = sum((_kw(r) for r in ("AND", "OR", "NOT")), ())
_CONST = sum((_kw(r) for r in ("BOOL", "NULL")), ()) + tuple(sorted(TRUTHY_WORDS))
_NS = _kw("GPU")


class QuackLexer(RegexLexer):
    """Pygments lexer for Quack / КРЯКА source files."""

    name = "Quack"
    aliases = ["quack", "kryaka", "кряка"]
    filenames = ["*.quack", "*.kry", "*.кря"]
    mimetypes = ["text/x-quack"]

    # IMPORTANT: Quack identifiers can include Cyrillic letters, so we use
    # \w-with-unicode in patterns and treat the script as UTF-8.
    flags = 0  # rely on default (Python 3 re is unicode-aware by default)

    tokens = {
        "root": [
            include("whitespace"),
            include("comments"),
            include("strings"),
            include("numbers"),

            # Keywords — order matters: longer / more-specific buckets first
            (words(_CONTROL, prefix=r"(?<![\w])", suffix=r"(?![\w])"),
             Keyword),
            (words(_DECL, prefix=r"(?<![\w])", suffix=r"(?![\w])"),
             Keyword.Declaration),
            (words(_IO, prefix=r"(?<![\w])", suffix=r"(?![\w])"),
             Name.Builtin),
            (words(_LOGIC, prefix=r"(?<![\w])", suffix=r"(?![\w])"),
             Operator.Word),
            (words(_CONST, prefix=r"(?<![\w])", suffix=r"(?![\w])"),
             Keyword.Constant),
            (words(_NS, prefix=r"(?<![\w])", suffix=r"(?![\w])"),
             Name.Namespace),

            # Identifiers (Cyrillic + Latin + digits)
            (r"[A-Za-z_Ѐ-ӿԀ-ԯ][\wЀ-ӿԀ-ԯ]*",
             Name),

            # Operators / punctuation
            (r"(==|!=|<=|>=|<|>|=|\+|-|\*|/|%|\.\.|\.|,|;|:)", Operator),
            (r"[\(\)\{\}\[\]]", Punctuation),
        ],

        "whitespace": [
            (r"\s+", Text),
        ],

        "comments": [
            (r"#[^\n]*", Comment.Single),
            (r"//[^\n]*", Comment.Single),
        ],

        "strings": [
            (r'"(?:\\.|[^"\\])*"', String.Double),
            (r"'(?:\\.|[^'\\])*'", String.Single),
        ],

        "numbers": [
            (r"\d+\.\d+", Number.Float),
            (r"\d+", Number.Integer),
        ],
    }
