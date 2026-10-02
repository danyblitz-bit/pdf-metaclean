# PDF MetaClean

Remove sensitive metadata from PDF files before you share them. One command, three modes.

## Why

A PDF exported from your business software can silently carry your **name, company, software, and even editing timestamps** — freelancers leak their identity this way all the time. PDF MetaClean strips it all.

## Install & Run

```bash
pip install -r requirements.txt

# Inspect what's hidden in a PDF
python -m tools.pdf-metaclean report.pdf

# See the full metadata list
python -m tools.pdf-metaclean report.pdf --verbose

# Write a sanitized copy
python -m tools.pdf-metaclean report.pdf --clean
# -> report_clean.pdf

# Overwrite the original
python -m tools.pdf-metaclean report.pdf --in-place

# Verify the tool works on your machine
python -m tools.pdf-metaclean --self-check
```

## Options

| Flag | Description |
|------|-------------|
| `--clean` | Write cleaned copy as `<name>_clean.pdf` |
| `--in-place` | Overwrite the original file after cleaning |
| `--verbose` | List all metadata found before cleaning |
| `--self-check` | Run a built-in correctness test |

## Why the byte-level strip

pypdf silently re-injects `/Producer` on every write. PDF MetaClean strips the PDF `/Info` trailer entry at the byte level after writing, so **no metadata can survive** — verified by the built-in self-check.

## Support the Project

PDF MetaClean is free and open source. Like it?

- [Get the DevTools Bundle](https://danyblitz.gumroad.com/l/zjkam) — 2 other tools + guide, pay what you want. Binaries are free here too; the bundle is support
- [Buy me a coffee](https://danyblitz.gumroad.com/l/hrvpiu) — one-time support

## Report a bug

Found a bug or something weird? Run:

```bash
python -m tools.pdf-metaclean --report
```

This opens a pre-filled email. Send it and I'll get notified automatically.

You can also email **danyblitz@googlemail.com** directly. Use the subject format:

```
[TOOL-REPORT] pdf-metaclean <what happened>
```

Attach the PDF or log output if you have one.

## License

MIT