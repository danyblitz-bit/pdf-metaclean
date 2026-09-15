"""PDF MetaClean — strip sensitive metadata before sharing PDFs."""
import io
import re
import sys
import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def audit(path: Path) -> dict:
    reader = PdfReader(str(path))
    meta = reader.metadata
    return {
        "pages": len(reader.pages),
        "metadata": {k: str(v) for k, v in meta.items()} if meta else {},
        "has_metadata": bool(meta),
    }


def clean(path: Path, out: Path) -> dict:
    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    raw = buf.getvalue().decode("latin-1")
    # pypdf injects /Producer; strip the /Info reference and dict from the trailer outright.
    # ponytail: flat-key Info dicts only; nested binary streams untouched. Upgrade to qpdf if exotic trailers appear.
    raw = re.sub(r"/Info \d+ \d+ R", "", raw)
    raw = re.sub(r"/Info <<[^>]*>>", "", raw)
    out.write_bytes(raw.encode("latin-1"))

    original = path.stat().st_size
    result = out.stat().st_size
    return {"cleaned": True, "input_bytes": original, "output_bytes": result, "saved_bytes": original - result}


def fmt(v: int) -> str:
    return f"{v/1024:.1f} KB"


def self_check() -> int:
    import tempfile

    from pypdf import PdfWriter

    buf = io.BytesIO()
    w = PdfWriter()
    w.add_blank_page(width=595, height=842)
    w.add_metadata({"/Author": "Sensitive Name", "/Title": "secret"})
    w.write(buf)

    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "in.pdf"
        out = Path(d) / "out.pdf"
        src.write_bytes(buf.getvalue())
        res = clean(src, out)
        assert res["cleaned"]
        assert "/Author" not in out.read_bytes().decode("latin-1"), "Author metadata survived"
        check = audit(out)
        assert not check["has_metadata"], f"Metadata remained: {check['metadata']}"
        assert check["pages"] == 1, "Page count changed"
    print("self-check OK: metadata stripped, page preserved")
    return 0


def report_to_email(message: str):
    import webbrowser
    from urllib.parse import quote

    subject = "[TOOL-REPORT] pdf-metaclean bug or issue"
    webbrowser.open(f"mailto:danyblitz@googlemail.com?subject={quote(subject)}&body={quote(message)}")


def main():
    parser = argparse.ArgumentParser(
        prog="pdf-metaclean",
        description="Remove sensitive metadata from PDF files. Print-audit a file or clean it in place.",
    )
    parser.add_argument("file", nargs="*", help="PDF file(s) to audit or clean")
    parser.add_argument("--self-check", action="store_true", help="Run internal correctness check")
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--clean", action="store_true", help="Write a cleaned copy as <name>_clean.pdf")
    output_mode.add_argument("--in-place", action="store_true", help="Overwrite the original after cleaning")
    parser.add_argument("--verbose", action="store_true", help="Show full metadata before cleaning")
    parser.add_argument("--report", action="store_true", help="Open a pre-filled email to report an issue")
    args = parser.parse_args()

    if args.self_check:
        sys.exit(self_check())

    if not args.file:
        parser.error("at least one PDF file is required (or use --self-check)")

    summary_lines = []
    for file_arg in args.file:
        p = Path(file_arg)
        if not p.exists():
            print(f"[SKIP] {p}: not found")
            summary_lines.append(f"[SKIP] {p}: not found")
            continue
        if p.suffix.lower() != ".pdf":
            print(f"[SKIP] {p}: not a PDF")
            summary_lines.append(f"[SKIP] {p}: not a PDF")
            continue

        info = audit(p)
        print(f"\n=== {p.name} ===")
        print(f"  Pages: {info['pages']}  |  Size: {fmt(p.stat().st_size)}")
        summary_lines.append(f"=== {p.name} === Pages: {info['pages']} Size: {fmt(p.stat().st_size)}")

        if not info["has_metadata"]:
            print("  Metadata: none found", "  (already clean)" if args.clean else "")
            if args.clean and not args.in_place:
                src = p.read_bytes()
                out = p.with_name(p.stem + "_clean.pdf")
                out.write_bytes(src)
                print(f"  Cleaned copy written to {out.name} (no metadata to remove, size unchanged)")
            continue

        if args.verbose:
            print("  Metadata found:")
            for k, v in info["metadata"].items():
                print(f"    {k}: {v[:80]}")
                summary_lines.append(f"    {k}: {v[:80]}")

        if args.clean or args.in_place:
            out_path = p if args.in_place else p.with_name(p.stem + "_clean.pdf")
            res = clean(p, out_path)
            print(f"  Cleaned -> {out_path.name} ({fmt(res['output_bytes'])}, {fmt(res['saved_bytes'])} saved)")
        else:
            fields = ", ".join(info["metadata"].keys()) or "(none printable)"
            print(f"  Metadata present: {fields}")
            print("  Use --clean to write a sanitized copy, or --in-place to overwrite.")

    if args.report:
        report_to_email("\n".join(summary_lines))
        print("\n  Email draft opened — send it and I'll get notified automatically.")


if __name__ == "__main__":
    main()