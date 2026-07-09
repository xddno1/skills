"""Remove iTeh watermark from ISO preview PDFs at the content-stream level.

The iTeh watermark is a Form XObject overlay called from a small extra content
stream (typically ~65-80 bytes) attached to each page. The body content lives in
separate streams. Different ISO PDFs use different XObject names (/Fm0, /FXX1,
etc.), so we detect watermark streams by size + presence of XObject Do operator
+ absence of text-drawing BT/ET blocks.

Usage:
    python remove_iteh_watermark.py <input.pdf> <output.pdf>

Requires: pip install pymupdf
"""
import re
import sys
from pathlib import Path
import fitz


# Regex for XObject draw: /NameSpace Do
_XOBJ_DO = re.compile(r'/[A-Za-z0-9]+\s+Do')


def _is_watermark_stream(raw: bytes) -> bool:
    """Heuristic: watermark streams are small, call an XObject, and have no BT."""
    if not raw:
        return False
    text = raw.decode("latin-1", errors="ignore")
    if len(raw) > 300:
        return False
    if not _XOBJ_DO.search(text):
        return False
    if "BT" in text:
        return False
    if "cm" not in text:
        return False
    return True


def remove_watermark(input_path: Path, output_path: Path) -> dict:
    doc = fitz.open(str(input_path))
    stats = {
        "pages": len(doc),
        "streams_cleared": 0,
        "per_page": [],
    }

    for page in doc:
        cleared_this_page = 0
        for xref in page.get_contents():
            raw = doc.xref_stream(xref) or b""
            if _is_watermark_stream(raw):
                doc.update_stream(xref, b" ")  # harmless no-op
                cleared_this_page += 1
        stats["streams_cleared"] += cleared_this_page
        stats["per_page"].append(cleared_this_page)

    doc.save(str(output_path), garbage=4, deflate=True, clean=True)
    doc.close()
    return stats


def verify_content_integrity(original_path: Path, cleaned_path: Path) -> dict:
    """Compare normalized body text of original and cleaned PDFs."""
    orig = fitz.open(str(original_path))
    clean = fitz.open(str(cleaned_path))

    def page_text(doc):
        parts = []
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text or span.get("color") == 0xE01A59:
                            continue
                        parts.append(text)
        return " ".join(parts).replace("\xa0", " ")

    orig_text = page_text(orig)
    clean_text = page_text(clean)
    orig.close()
    clean.close()

    return {
        "intact": orig_text == clean_text,
        "orig_chars": len(orig_text),
        "clean_chars": len(clean_text),
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python remove_iteh_watermark.py <input.pdf> <output.pdf>")
        sys.exit(1)
    in_p = Path(sys.argv[1])
    out_p = Path(sys.argv[2])
    if not in_p.exists():
        print(f"Input not found: {in_p}")
        sys.exit(1)

    stats = remove_watermark(in_p, out_p)
    in_size = in_p.stat().st_size
    out_size = out_p.stat().st_size

    verify = verify_content_integrity(in_p, out_p)

    print(f"Input : {in_p}  ({in_size} bytes)")
    print(f"Output: {out_p}  ({out_size} bytes)")
    print(f"Pages : {stats['pages']}")
    print(f"Watermark streams cleared: {stats['streams_cleared']}")
    pages_no_wm = sum(1 for n in stats["per_page"] if n == 0)
    if pages_no_wm:
        print(f"Pages without detected watermark: {pages_no_wm}")
    print(f"Body content intact: {verify['intact']} ({verify['clean_chars']} chars)")


if __name__ == "__main__":
    main()
