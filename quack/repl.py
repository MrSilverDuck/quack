"""
Quack REPL — interactive shell for the Russian-English programming language.

🦆 Кря! Запускается через `quack` без аргументов или `python -m quack`.

Features:
  • Autocomplete across all 364 keywords (Cyrillic + Latin)
  • Persistent VM state — variables/functions live across prompts
  • Multiline input — opens automatically when `{` is unclosed
  • Syntax highlighting via Pygments lexer
  • Built-in examples — `:examples` to list, `:run <name>` to execute
  • Command history — saved to ~/.quack_history

Special commands (start with `:`):
  :help / :h        — show this help
  :keywords [q]     — list keywords; optional filter
  :examples         — list bundled examples
  :run <name>       — execute a bundled example
  :vars             — show currently defined globals
  :reset            — wipe VM state, start fresh
  :clear / :c       — clear screen
  :exit / :q / EOF  — quit (Ctrl+D also works)

If `prompt_toolkit` is not installed, falls back to a simple `input()` loop
so the REPL still works on minimal Python installs.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

# Core interpreter pieces — we drive them directly so VM state persists
from .quack import (
    KEYWORDS,
    TRUTHY_WORDS,
    QuackLexer,
    QuackParser,
    QuackVM,
    QUACK_EXAMPLES,
    _preregister_word_defs,
)
from . import __version__


BANNER = r"""
   __         _  _   _   _   _   _
  /  \    Quack / КРЯКА — v{version}
 ( -> )   364 keywords · 9 languages · MIT
  \__/    type :help  for commands · :exit to quit
"""


# ── Prompt-toolkit availability ────────────────────────────────
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.lexers import PygmentsLexer
    from prompt_toolkit.styles import Style
    from prompt_toolkit.formatted_text import HTML
    _HAS_PTK = True
except ImportError:
    _HAS_PTK = False

# ── Pygments lexer (optional too) ──────────────────────────────
try:
    from .lexer import QuackLexer as PygmentsQuackLexer
    _HAS_LEXER = True
except ImportError:
    _HAS_LEXER = False


# ══════════════════════════════════════════════════════════════
# ANSI helpers (work without prompt_toolkit too)
# ══════════════════════════════════════════════════════════════
def _supports_color() -> bool:
    """Best-effort check for ANSI support."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        # Windows 10+ supports ANSI when VT mode is enabled (Win Terminal does it).
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return True


_COLOR = _supports_color()


def _c(text: str, code: str) -> str:
    """Wrap text in ANSI color, or return as-is if colors disabled."""
    if not _COLOR:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def _yellow(t: str) -> str: return _c(t, "33")
def _cyan(t: str) -> str:   return _c(t, "36")
def _green(t: str) -> str:  return _c(t, "32")
def _red(t: str) -> str:    return _c(t, "31")
def _dim(t: str) -> str:    return _c(t, "2")
def _bold(t: str) -> str:   return _c(t, "1")


# ══════════════════════════════════════════════════════════════
# REPL core
# ══════════════════════════════════════════════════════════════
class QuackREPL:
    """Interactive Quack shell with persistent VM state."""

    def __init__(self) -> None:
        self.vm = QuackVM()
        self._session = None  # lazy-built on first prompt (avoids non-TTY crash at init)
        self.line_no = 0

    @property
    def session(self):
        """Build PromptSession lazily so non-TTY environments don't crash on import."""
        if self._session is None and _HAS_PTK:
            try:
                self._session = self._build_session()
            except Exception:
                # Non-TTY (no Windows console buffer, piped stdin, etc.) — fall back
                # to plain input(). The REPL still works, just no autocomplete.
                self._session = False  # sentinel: tried and failed
        return self._session if self._session else None

    # ─── Session setup ────────────────────────────────────────
    def _build_session(self):
        history_path = Path.home() / ".quack_history"
        try:
            history = FileHistory(str(history_path))
        except Exception:
            history = None

        # Completer: every keyword + every truthy/falsy word + builtins from VM globals
        words: list[str] = sorted({
            *KEYWORDS.keys(),
            *TRUTHY_WORDS,
            *self.vm.globals.keys(),
        })
        completer = WordCompleter(words, ignore_case=False, sentence=False)

        style = Style.from_dict({
            "prompt": "ansibrightyellow bold",
            "continuation": "ansiyellow",
        })

        lexer = PygmentsLexer(PygmentsQuackLexer) if _HAS_LEXER else None

        return PromptSession(
            history=history,
            completer=completer,
            style=style,
            lexer=lexer,
            include_default_pygments_style=False,
            multiline=False,  # we handle multiline ourselves via brace counting
        )

    # ─── Multiline detection ─────────────────────────────────
    @staticmethod
    def _needs_more(buf: str) -> bool:
        """Naive but effective: balanced { } detection ignoring strings/comments."""
        depth = 0
        i = 0
        in_string: str | None = None
        while i < len(buf):
            ch = buf[i]
            if in_string:
                if ch == "\\" and i + 1 < len(buf):
                    i += 2
                    continue
                if ch == in_string:
                    in_string = None
                i += 1
                continue
            if ch in ('"', "'"):
                in_string = ch
            elif ch == "#":
                # Skip until end of line
                nl = buf.find("\n", i)
                if nl == -1:
                    break
                i = nl
                continue
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            i += 1
        return depth > 0

    # ─── Prompt strings ──────────────────────────────────────
    def _prompt(self, more: bool = False) -> str:
        if more:
            return "..  "
        return f"кря[{self.line_no}]» "

    # ─── Read one logical statement (multiline aware) ────────
    def _read_input(self) -> str | None:
        """Returns input string, or None on EOF/Ctrl+D."""
        buf_lines: list[str] = []
        try:
            while True:
                more = bool(buf_lines)
                if self.session is not None:
                    line = self.session.prompt(self._prompt(more))
                else:
                    sys.stdout.write(self._prompt(more))
                    sys.stdout.flush()
                    line = sys.stdin.readline()
                    if not line:  # EOF
                        if buf_lines:
                            break  # treat as final
                        return None
                    line = line.rstrip("\n")

                buf_lines.append(line)
                joined = "\n".join(buf_lines)
                if not self._needs_more(joined):
                    return joined
        except (EOFError, KeyboardInterrupt):
            if buf_lines:
                # Cancel the current multiline input
                print(_dim("\n(input cancelled)"))
                return ""
            raise

    # ─── Execute Quack source on the persistent VM ──────────
    def _execute(self, source: str) -> None:
        """Run source through Lexer/Parser/VM with state persisted."""
        if not source.strip():
            return
        try:
            _preregister_word_defs(source)
            tokens = QuackLexer(source).tokenize()
            ast = QuackParser(tokens).parse()
            output = self.vm.execute(ast)
            if output:
                print(output)
        except SyntaxError as e:
            print(_red(f"❌ syntax: {e}"))
        except (NameError, TypeError, AttributeError, RuntimeError) as e:
            print(_red(f"❌ runtime: {e}"))
        except Exception as e:  # pragma: no cover
            print(_red(f"💥 internal: {e}"))

    # ─── Special commands ────────────────────────────────────
    def _handle_command(self, raw: str) -> bool:
        """Returns True if loop should continue, False to quit."""
        cmd, _, args = raw.strip().lstrip(":").partition(" ")
        cmd = cmd.lower()

        if cmd in ("exit", "quit", "q"):
            return False

        if cmd in ("help", "h", "?"):
            self._cmd_help()
        elif cmd in ("keywords", "kw"):
            self._cmd_keywords(args.strip())
        elif cmd in ("examples", "ex"):
            self._cmd_examples()
        elif cmd in ("run",):
            self._cmd_run(args.strip())
        elif cmd in ("vars", "v"):
            self._cmd_vars()
        elif cmd in ("reset", "r"):
            self.vm = QuackVM()
            self._session = None  # force rebuild (new globals → new completer)
            print(_green("🦆 VM reset. Globals wiped, builtins reloaded."))
        elif cmd in ("clear", "c", "cls"):
            os.system("cls" if os.name == "nt" else "clear")
        elif cmd in ("version", "ver"):
            print(f"Quack v{__version__} (КРЯКА)")
        else:
            print(_yellow(f"unknown command: :{cmd}"))
            print(_dim("type :help for the list"))
        return True

    def _cmd_help(self) -> None:
        print(_bold("\nQuack REPL — special commands"))
        rows = [
            (":help / :h",        "show this help"),
            (":keywords [filter]", "list keywords (optional substring filter)"),
            (":examples",          "list bundled example programs"),
            (":run <name>",        "execute a bundled example"),
            (":vars",              "show currently defined variables/functions"),
            (":reset",             "wipe VM state and start fresh"),
            (":clear",             "clear the screen"),
            (":version",           "print Quack version"),
            (":exit / Ctrl+D",     "quit the REPL"),
        ]
        for cmd, desc in rows:
            print(f"  {_cyan(cmd):28}  {desc}")
        print(_dim("\nMultiline: when `{` is open, the REPL waits for `}` before running."))
        print()

    def _cmd_keywords(self, filt: str) -> None:
        words = sorted(set(KEYWORDS.keys()))
        if filt:
            words = [w for w in words if filt.lower() in w.lower()]
        if not words:
            print(_dim(f"no keywords match '{filt}'"))
            return
        # 5 columns of ~14 chars each — friendly on 80-col terminals
        col = max(len(w) for w in words) + 2
        per_row = max(1, 80 // col)
        print(_bold(f"{len(words)} keyword(s)" + (f" matching '{filt}'" if filt else "")))
        for i, w in enumerate(words):
            sep = "\n" if (i + 1) % per_row == 0 else ""
            sys.stdout.write(_yellow(w.ljust(col)) + sep)
        if len(words) % per_row != 0:
            print()
        print()

    def _cmd_examples(self) -> None:
        print(_bold("Bundled examples:"))
        for name in QUACK_EXAMPLES:
            first_line = QUACK_EXAMPLES[name].lstrip().splitlines()[0]
            print(f"  {_cyan(name):22}  {_dim(first_line[:50])}")
        print(_dim("\nrun one with:  :run <name>"))

    def _cmd_run(self, name: str) -> None:
        if not name:
            print(_yellow("usage: :run <example_name>  (try :examples)"))
            return
        if name not in QUACK_EXAMPLES:
            print(_red(f"no such example: {name}"))
            return
        src = QUACK_EXAMPLES[name]
        print(_dim(f"--- running example: {name} ---"))
        self._execute(src)
        print(_dim("--- end ---"))

    def _cmd_vars(self) -> None:
        # Filter out the VM's own builtins by checking against a fresh VM
        baseline_vm = QuackVM()
        user_vars = {
            k: v for k, v in self.vm.globals.items()
            if k not in baseline_vm.globals
        }
        if not user_vars:
            print(_dim("no user-defined variables yet"))
            return
        print(_bold(f"{len(user_vars)} user variable(s):"))
        for name, val in user_vars.items():
            preview = repr(val)
            if len(preview) > 60:
                preview = preview[:57] + "..."
            print(f"  {_cyan(name):20}  = {preview}")

    # ─── Main loop ────────────────────────────────────────────
    def run(self) -> int:
        print(_yellow(BANNER.format(version=__version__)))
        if not _HAS_PTK:
            print(_dim("(prompt_toolkit not installed — autocomplete & history disabled)"))
            print(_dim(" install with:  pip install prompt_toolkit pygments\n"))

        while True:
            try:
                source = self._read_input()
            except KeyboardInterrupt:
                print(_dim("\n(KeyboardInterrupt — :exit to quit)"))
                continue
            except EOFError:
                source = None

            if source is None:
                print(_yellow("\n🦆 Кря! Пока!"))
                return 0

            if not source.strip():
                continue

            self.line_no += 1

            if source.lstrip().startswith(":"):
                if not self._handle_command(source):
                    print(_yellow("🦆 Кря! Пока!"))
                    return 0
                continue

            self._execute(source)


def main() -> int:
    """Entry point — `quack` (no args) lands here."""
    return QuackREPL().run()


if __name__ == "__main__":
    raise SystemExit(main())
