# Quack / КРЯКА 🦆

> A Russian-English mixed programming language. Pirate-themed, esoteric,
> with 364 keywords across 9 natural languages, a teacher mode, and a poet mode.
>
> Built by **Nightbox LLC** as part of the [SilverDuck](https://github.com/MrSilverDuck/unigpu) ecosystem.
>
> Short link: [mrsilverduck.lif-6.com/quack](https://mrsilverduck.lif-6.com/quack)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/MrSilverDuck/quack?include_prereleases)](https://github.com/MrSilverDuck/quack/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)

---

## Live demo — works right now 🦆

### From the CLI (v0.2.0+)

```bash
pip install quack-lang
quack             # interactive REPL with autocomplete
quack -c "кряк('Привет, кремний!')"
quack -e gpu_demo # run a bundled example
quack file.quack  # run a script
```

Inside the REPL: type `:help` for commands, `:keywords` to browse all 364, `:examples` to discover demos, `:vars` to inspect state. State persists across prompts:

```text
кря[1]» пусть x = 21
кря[2]» fn двойной(n) { вернуть n * 2 }
кря[3]» кряк("x*2 =", двойной(x))
x*2 = 42
кря[4]» :exit
🦆 Кря! Пока!
```

### From Python

```python
from quack import run_quack

result = run_quack('''
кряк("Привет, кремний!")
пусть x = 21
кряк("21 * 2 =", x * 2)

fn факториал(n) {
    если n <= 1 { вернуть 1 }
    вернуть n * факториал(n - 1)
}

кряк("10! =", факториал(10))
кряк("20! =", факториал(20))
''')

print(result["output"])
```

**Real output** (measured on Linux WSL Ubuntu 24.04, Python 3.12.3):

```
Привет, кремний!
21 * 2 = 42
10! = 3628800
20! = 2432902008176640000
```

89 tokens · 9 AST nodes · **11 ms** end-to-end on cold cache.

If `unigpu_ffi.dll` is also on the system, GPU primitives are wired in too:

```quack
кряк("Найдено GPU:", гпу.найди())
```

```
Найдено GPU: 3
```

(One physical AMD RX 7700 XT visible through 3 backends: Direct/D3DKMT, HIP, CPU fallback.)

---

## What is Quack

**Quack** (КРЯКА) is what happens when you let a duck design a programming language during a long Russian winter.

Most languages pick one human language. Quack picks **nine**: Russian, English, Ukrainian, Spanish, Chinese, French, German, Italian, Japanese — and lets you mix keywords from any of them in the same program. The interpreter doesn't care.

```quack
кря
сказать "Привет, мир!"
let x = 42
если x > 0 тогда
    print "positive"
fin
```

That's valid Quack. So is the same thing in pure English, or pure Russian, or any mix you like.

### Highlights

- **364 keywords** across 9 languages — pick your dialect
- **Zoomer mode** — slang aliases (`vibe`, `sus`, `slay`, `кринж`)
- **Teacher mode** — interactive tutor that explains errors and concepts
- **Poet mode** — generative writing assistant that speaks Quack
- **Optional GPU** — falls back to pure Python; uses [UniGPU](https://github.com/MrSilverDuck/unigpu) FFI when available
- **Pure stdlib** — no runtime dependencies for the core interpreter

## Install

From source (preferred while in beta):

```bash
git clone https://github.com/MrSilverDuck/quack.git
cd quack
pip install -e .
```

Or from PyPI once published:

```bash
pip install quack-lang
```

## Run

```bash
# Run a .quack file
python -m quack examples/sample.quack

# Or via the installed entry point
quack examples/sample.quack
```

From Python:

```python
from quack import run_quack

run_quack('''
    кря
    let n = 10
    повторить n раз:
        сказать "🦆"
''')
```

## Modes

| Module | What it does |
|--------|-------------|
| `quack.quack` | The core interpreter (`run_quack`, `KEYWORDS`, `TRUTHY_WORDS`) |
| `quack.repl` | Interactive REPL — `quack` command launches it (`prompt_toolkit`-powered) |
| `quack.lexer` | Pygments lexer (registered as a `pygments.lexers` entry point) |
| `quack.quack_vm` | A small bytecode VM and runtime |
| `quack.quack_teacher` | Interactive teacher mode — explains syntax, errors, idioms |
| `quack.quack_poet` | Generative poet mode — produces Quack from natural language |

## Editor support

- **VS Code** — install the bundled extension (`vscode-quack/`) for syntax highlighting on `.quack` files. See [`vscode-quack/README.md`](vscode-quack/README.md) for build/install steps.
- **Sphinx, Jupyter, mkdocs, Pelican, …** — `pip install quack-lang` registers a Pygments lexer; ` ```quack ` code blocks light up automatically.
- **Anywhere with ANSI** — the REPL itself colorizes input via `prompt_toolkit + pygments`.

## Examples

See `examples/sample.quack` and `examples/runtime.quack`. Programs in the wild often look like this:

```quack
кря
переменная имя = "Captain Silverduck"
if имя contains "Silver" then
    сказать "🏴‍☠️ Аррр, я тебя знаю, " + имя
end
```

## Status

🟢 **0.2.0** — Interactive REPL with autocomplete across all 364 keywords, Pygments lexer for `.quack` files, VS Code extension, fixed `python -m quack file.quack` output bug.

🟡 Syntax is largely stable but the keyword tables, especially zoomer-mode aliases, may grow. Issues and PRs welcome.

The optional GPU acceleration looks for `unigpu_ffi.{so,dll,dylib}` (from the [UniGPU](https://github.com/MrSilverDuck/unigpu) repo). Without it, Quack runs entirely in CPython — no SDKs needed.

## Roadmap

- **0.2.0** *(this release)* — REPL with completion, Pygments lexer, VS Code grammar
- **0.3.0** — Compiled-bytecode mode via `quack.quack_vm`, JIT path through UniGPU IR (Quack → AMD/NVIDIA GPU)
- **0.4.0** — More natural-language packs (Arabic, Hindi, Korean), Marketplace publish for VS Code extension

## License

[MIT](LICENSE) © 2026 Nightbox LLC.

`Quack` and `КРЯКА` are trademarks of Nightbox LLC. The code is yours under MIT.

---

🦆 *Кря-кря-кря! Кря — на любом языке.*
