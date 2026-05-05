# Contributing to Quack 🦆

Quack is a small project. The bar for contributing is low.

## Quick PR checklist

- [ ] CI is green (matrix Python 3.10–3.12 × Linux/Windows/macOS)
- [ ] `KEYWORDS` count is still 364 (or you've intentionally added some — say so in the PR)
- [ ] You've run `python -m quack examples/sample.quack` locally
- [ ] If you added a new keyword: it's documented in the README's keyword table

## What we'd love

- More natural-language packs (Arabic, Hindi, Korean — open an issue first)
- Better error messages — point at the offending token, not the whole line
- A real Quack → Python/Rust/C transpiler (currently there's only a tiny Russian-ABC → Python proof-of-concept in `silverduck/console.py`)
- A REPL with line-editing (rustyline-style)
- Syntax highlighting for VS Code / Sublime / Vim
- Writing example programs (`examples/`)

## What gets a longer review

- Changes that break existing keyword names or AST shape
- New runtime dependencies — we like the "stdlib only" property of the core
- Public API changes (`run_quack`, `KEYWORDS`, `TRUTHY_WORDS`)

## Reporting bugs

Include:
- Python version
- OS
- The Quack program that misbehaves
- What you expected
- What `run_quack(prog)` returned (success, error, output, time_s)

🦆 *Кря.*
