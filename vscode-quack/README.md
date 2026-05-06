# Quack / КРЯКА — VS Code

Syntax highlighting for **[Quack](https://github.com/MrSilverDuck/quack)** — the Russian-English mixed programming language with 364 keywords across 9 natural languages.

```quack
fn факториал(n) {
    если n <= 1 { вернуть 1 }
    вернуть n * факториал(n - 1)
}
кряк("20! =", факториал(20))
```

## Features

- 353 keywords highlighted (`кряк`, `пусть`, `если`, `функция`, `let`, `if`, `fn`, `print`…)
- Both `.quack` and `.кря` file extensions
- Cyrillic-aware word boundaries (so `крякнуть` doesn't highlight as `кря` + `кнуть`)
- Bracket matching, auto-closing pairs, comments (`#`, `//`, `/* */`)

## Install (manual)

Until this is on the Marketplace:

```bash
git clone https://github.com/MrSilverDuck/quack.git
cd quack/vscode-quack
npm install -g @vscode/vsce      # one-time
vsce package                      # produces quack-lang-0.2.0.vsix
code --install-extension quack-lang-0.2.0.vsix
```

## Companion: REPL + interpreter

```bash
pip install quack-lang
quack             # interactive REPL
quack file.quack  # run a script
```

Full docs: <https://github.com/MrSilverDuck/quack>

## License

[MIT](../LICENSE) © 2026 Nightbox LLC.
