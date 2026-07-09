#!/usr/bin/env python3
"""
Convert a scanned (image-only) PDF into a Searchable PDF.

Preserves the original visual appearance while adding an invisible
OCR text layer on top, making the document searchable and copyable.

Usage:
    python -m long_pdf_reader.ocr_to_searchable_pdf <input.pdf> <output.pdf>

Options:
    --ocr-engine NAME     ocr backend: auto, pymupdf, pytesseract, easyocr
    --ocr-lang LANG       OCR language (default: eng)
    --ocr-dpi DPI         render DPI for OCR (default: 300)
    --force-ocr           OCR every page even if text layer exists
    --pages SPEC          process only specific pages (e.g. 1-10,15,20)
    --keep-text           keep existing text layer; only add OCR for scan pages
"""

import sys
import re

from .ocr_utils import is_scan_page, get_ocr_engine


def parse_range(spec):
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


def fit_text_in_rect(page, rect, text, fontname="china-s", max_fontsize=24, min_fontsize=4):
    """
    Try to insert text into a rectangle with an appropriate font size.
    Uses render_mode=3 (invisible text) for the text layer.
    Returns True if successful.
    """
    if not text or not text.strip():
        return False

    # Start with a heuristic fontsize based on rect height
    # Assume roughly 1.2x line height
    fontsize = min(max_fontsize, max(min_fontsize, rect.height / 1.5))

    for _ in range(20):  # max iterations
        if fontsize < min_fontsize:
            break
        try:
            rc = page.insert_textbox(
                rect,
                text,
                fontsize=fontsize,
                fontname=fontname,
                render_mode=3,       # invisible text
                overlay=True,        # draw on top of existing content
                align=0,             # left align
                color=(0, 0, 0),     # color doesn't matter for invisible text
            )
            # rc is overflow indicator: 0 = all fit, >0 = overflow chars
            if rc == 0:
                return True
            # Reduce font size and retry
            fontsize *= 0.85
        except Exception:
            # Some fonts may not support certain chars; fallback to smaller size
            fontsize *= 0.85

    # Last resort: use minimum font size and accept truncation
    try:
        page.insert_textbox(
            rect, text, fontsize=min_fontsize, fontname=fontname,
            render_mode=3, overlay=True, align=0, color=(0, 0, 0)
        )
        return True
    except Exception:
        return False


def process_pdf(input_path, output_path, ocr_engine="auto", ocr_lang="eng",
                ocr_dpi=300, force_ocr=False, page_nums=None, keep_text=False):
    import fitz

    doc = fitz.open(input_path)
    total = len(doc)

    if page_nums is None:
        page_nums = list(range(1, total + 1))

    # Pre-init OCR engine so we fail fast if unavailable
    engine = get_ocr_engine(ocr_engine, ocr_lang)
    print(f"Using OCR engine: {engine.name}")

    processed = 0
    ocr_applied = 0

    for pnum in page_nums:
        idx = pnum - 1
        if idx < 0 or idx >= total:
            continue
        page = doc.load_page(idx)
        processed += 1

        need_ocr = force_ocr or is_scan_page(page)
        if not need_ocr:
            if (processed - 1) % 10 == 0 or processed == len(page_nums):
                print(f"  Page {pnum}/{total}: text layer OK")
            continue

        print(f"  Page {pnum}/{total}: running OCR ...")
        try:
            blocks = engine.extract_blocks(page, dpi=ocr_dpi)
        except Exception as e:
            print(f"    ERROR on page {pnum}: {e}")
            continue

        if not blocks:
            print(f"    Page {pnum}: no text detected")
            continue

        # Remove existing text if not keeping it (to avoid duplicate search results)
        if not keep_text:
            # Add a redaction annotation covering the whole page for text only,
            # but we want to keep images. PyMuPDF redaction can remove text.
            # A simpler approach: we just overlay invisible text; duplicates in
            # search results are acceptable for most use cases.
            # For high fidelity, advanced users can pre-process to remove text.
            pass

        added = 0
        for text, bbox in blocks:
            text = text.strip()
            if not text:
                continue
            # Ensure bbox is valid
            x0, y0, x1, y1 = bbox
            if x1 <= x0 or y1 <= y0:
                continue
            rect = fitz.Rect(x0, y0, x1, y1)
            if fit_text_in_rect(page, rect, text):
                added += 1

        ocr_applied += 1
        print(f"    Added {added} invisible text blocks")

    # Save with garbage collection and deflate to keep size reasonable
    doc.save(
        output_path,
        garbage=4,
        deflate=True,
        clean=True,
    )
    doc.close()

    print(f"\nDone: {output_path}")
    print(f"  Total pages: {total}")
    print(f"  Processed:   {processed}")
    print(f"  OCR applied: {ocr_applied}")


def parse_args(argv):
    args = {
        "input": None,
        "output": None,
        "ocr_engine": "auto",
        "ocr_lang": "eng",
        "ocr_dpi": 300,
        "force_ocr": False,
        "pages": None,
        "keep_text": False,
    }
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--ocr-engine":
            i += 1
            args["ocr_engine"] = argv[i]
        elif a == "--ocr-lang":
            i += 1
            args["ocr_lang"] = argv[i]
        elif a == "--ocr-dpi":
            i += 1
            args["ocr_dpi"] = int(argv[i])
        elif a == "--force-ocr":
            args["force_ocr"] = True
        elif a == "--pages":
            i += 1
            args["pages"] = argv[i]
        elif a == "--keep-text":
            args["keep_text"] = True
        elif not a.startswith("-"):
            if args["input"] is None:
                args["input"] = a
            elif args["output"] is None:
                args["output"] = a
        i += 1
    return args


def main():
    args = parse_args(sys.argv)

    if not args["input"] or not args["output"]:
        print(__doc__)
        sys.exit(1)

    page_nums = None
    if args["pages"]:
        page_nums = parse_range(args["pages"])

    process_pdf(
        args["input"],
        args["output"],
        ocr_engine=args["ocr_engine"],
        ocr_lang=args["ocr_lang"],
        ocr_dpi=args["ocr_dpi"],
        force_ocr=args["force_ocr"],
        page_nums=page_nums,
        keep_text=args["keep_text"],
    )


if __name__ == "__main__":
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
