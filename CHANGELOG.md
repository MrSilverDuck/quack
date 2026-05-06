# Changelog

All notable changes to **Quack / КРЯКА** are documented here. Format roughly follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/).

## [0.2.0] — 2026-05-05

### Added
- **Interactive REPL** (`quack` command, no args) — `prompt_toolkit`-powered with:
  - Autocomplete across all 364 keywords (Cyrillic + Latin) plus user-defined globals
  - Persistent VM state — variables and functions live across prompts
  - Multiline detection via brace counting (string- and comment-aware)
  - Command history saved to `~/.quack_history`
  - Special commands: `:help`, `:keywords [filter]`, `:examples`, `:run <name>`, `:vars`, `:reset`, `:clear`, `:version`, `:exit`
  - Graceful fallback to plain `input()` on non-TTY environments
- **Pygments lexer** (`quack.lexer.QuackLexer`) — registered as a `pygments.lexers` entry point so Sphinx, Jupyter, mkdocs, and any other Pygments consumer auto-highlight ` ```quack ` blocks
- **VS Code extension** (`vscode-quack/`) — TextMate grammar with 353 keywords highlighted, generated programmatically from the live `KEYWORDS` table so it can never drift from the interpreter
- **CLI flags** — `quack -c "<code>"` for one-liners, `quack -e <name>` to run bundled examples, `quack -V` / `--version`, `quack -h` / `--help`
- **`QUACK_EXAMPLES`** re-exported from the package root for embedded use

### Fixed
- `python -m quack file.quack` previously discarded program output (called `run_quack(src)` without printing the result). Now properly prints `result["output"]` and propagates the exit code on failure.
- Cyrillic stdout on Windows — `__main__.py` now reconfigures `sys.stdout` / `sys.stderr` to UTF-8 so `print('кряк')` no longer raises `UnicodeEncodeError` on cp1252 consoles.

### Changed
- `pyproject.toml`: added `prompt_toolkit>=3.0` and `pygments>=2.14` to runtime dependencies; both are tiny pure-Python packages on every supported platform.
- `quack/__init__.py` re-exports `QUACK_EXAMPLES` and bumps `__version__` to `0.2.0`.

### Notes
- The interpreter core (`quack.quack`) is byte-for-byte unchanged — 0.2.0 is purely tooling. Any 0.1.x program runs identically.
- VS Code extension is not yet on the Marketplace; install locally via `vsce package` + `code --install-extension`. Marketplace publish is roadmap **0.4.0**.

## [0.1.1-beta] — 2026-05-05

Initial public source drop. MIT licensed.

- 364 keywords across 9 natural languages
- Lexer / Parser / VM pipeline implemented in pure Python
- `run_quack(source)` programmatic entry point
- `python -m quack file.quack` CLI runner (output-discard bug, fixed in 0.2.0)
- Bundled examples under `examples/`
- Optional GPU acceleration via [UniGPU](https://github.com/MrSilverDuck/unigpu) FFI

[0.2.0]:     https://github.com/MrSilverDuck/quack/releases/tag/v0.2.0
[0.1.1-beta]: https://github.com/MrSilverDuck/quack/releases/tag/v0.1.1-beta
