# Tiresias

Tiresias is a deterministic gatekeeper that performs a pre-mortem design review on Markdown documents.

## Install

```bash
pip install -e .[dev]
```

## CLI

```bash
tiresias review path/to/doc.md
```

### Windows

If your shell can't find the `tiresias` command, run it via the venv or module entrypoint:

```powershell
.\.venv\Scripts\tiresias.exe review path\to\doc.md
```

```powershell
python -m tiresias review path\to\doc.md
```

- Writes outputs to `.tiresias.out/review.json` and `.tiresias.out/review.md`
- Exits with code `2` when `--fail-on` is met or exceeded

## Philosophy

- This tool is a gatekeeper, not an assistant.
- Favor determinism over cleverness.
- Favor structure over prose.
