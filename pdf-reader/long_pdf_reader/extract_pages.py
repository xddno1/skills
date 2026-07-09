#!/usr/bin/env python3
"""
Extract text from specific page ranges of a PDF.

Supports both native text layer extraction and OCR for scan pages.

Usage:
    python -m long_pdf_reader.extract_pages <input.pdf> <page_spec> [output.txt]

page_spec examples:
    10              single page
    10-20           inclusive range
    10-20,25,30-35  comma-separated ranges

Options:
    --json                output as JSON with per-page text
    --ocr                 enable OCR for image-only (scan) pages
    --ocr-engine NAME     ocr backend: auto, pymupdf, pytesseract, easyocr
    --ocr-lang LANG       OCR language (default: eng)
    --ocr-dpi DPI         render DPI for OCR (default: 300)
    --force-ocr           OCR every page even if text layer exists
    --ocr-info            print available OCR engines and exit
"""

import json
import sys
import re

from .ocr_utils import extract_page_text


def check_deps():
    try:
        import fitz
        return "fitz"
    except ImportError:
        pass
    try:
        import pypdf
        return "pypdf"
    except ImportError:
        pass
    print("ERROR: No PDF library found. Install one of:")
    print("  pip install pymupdf      # recommended")
    print("  pip install pypdf        # fallback")
    sys.exit(1)


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


def extract_fitz(pdf_path, page_nums, use_ocr=False, ocr_engine="auto",
                 ocr_lang="eng", ocr_dpi=300, force_ocr=False):
    import fitz

    doc = fitz.open(pdf_path)
    results = []
    for pnum in page_nums:
        idx = pnum - 1
        if 0 <= idx < len(doc):
            page = doc.load_page(idx)
            text = extract_page_text(
                page, use_ocr=use_ocr, engine_name=ocr_engine,
                language=ocr_lang, dpi=ocr_dpi, force_ocr=force_ocr
            )
            results.append({
                "page_num": pnum,
                "text": text,
            })
    doc.close()
    return results


def extract_pypdf(pdf_path, page_nums):
    import pypdf
    reader = pypdf.PdfReader(pdf_path)
    results = []
    for pnum in page_nums:
        idx = pnum - 1
        if 0 <= idx < len(reader.pages):
            text = reader.pages[idx].extract_text() or ""
            results.append({
                "page_num": pnum,
                "text": text,
            })
    return results


def parse_args(argv):
    args = {
        "pdf_path": None,
        "page_spec": None,
        "out_path": None,
        "as_json": False,
        "use_ocr": False,
        "ocr_engine": "auto",
        "ocr_lang": "eng",
        "ocr_dpi": 300,
        "force_ocr": False,
        "ocr_info": False,
    }
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            args["as_json"] = True
        elif a == "--ocr":
            args["use_ocr"] = True
        elif a == "--ocr-engine":
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
        elif a == "--ocr-info":
            args["ocr_info"] = True
        elif not a.startswith("-"):
            if args["pdf_path"] is None:
                args["pdf_path"] = a
            elif args["page_spec"] is None:
                args["page_spec"] = a
            else:
                args["out_path"] = a
        i += 1
    return args


def main():
    args = parse_args(sys.argv)

    if args["ocr_info"]:
        from .ocr_utils import ocr_engine_info
        print(ocr_engine_info())
        sys.exit(0)

    if not args["pdf_path"] or not args["page_spec"]:
        print(__doc__)
        sys.exit(1)

    page_nums = parse_range(args["page_spec"])
    if not page_nums:
        print("ERROR: No valid pages specified.")
        sys.exit(1)

    backend = check_deps()
    if backend == "fitz":
        results = extract_fitz(
            args["pdf_path"], page_nums,
            use_ocr=args["use_ocr"],
            ocr_engine=args["ocr_engine"],
            ocr_lang=args["ocr_lang"],
            ocr_dpi=args["ocr_dpi"],
            force_ocr=args["force_ocr"],
        )
    else:
        if args["use_ocr"] or args["force_ocr"]:
            print("ERROR: OCR requires PyMuPDF (pymupdf). pypdf backend does not support OCR.")
            print("Install: pip install pymupdf")
            sys.exit(1)
        results = extract_pypdf(args["pdf_path"], page_nums)

    if args["as_json"]:
        output = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        lines = []
        for r in results:
            lines.append(f"--- Page {r['page_num']} ---")
            lines.append(r["text"])
            lines.append("")
        output = "\n".join(lines)

    if args["out_path"]:
        with open(args["out_path"], "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Extracted {len(results)} pages to: {args['out_path']}")
    else:
        print(output)


if __name__ == "__main__":
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
