#!/usr/bin/env python3
"""
Build a searchable index from a PDF and its structure file.

Supports both native text layer extraction and OCR for scan pages.

Usage:
    python -m long_pdf_reader.build_index <input.pdf> <structure.json> [output.json]

Options:
    --ocr                 enable OCR for image-only (scan) pages
    --ocr-engine NAME     ocr backend: auto, pymupdf, pytesseract, easyocr
    --ocr-lang LANG       OCR language (default: eng)
    --ocr-dpi DPI         render DPI for OCR (default: 300)
    --force-ocr           OCR every page even if text layer exists
    --ocr-info            print available OCR engines and exit

Output JSON format:
    {
        "source_pdf": "...",
        "total_pages": 300,
        "pages": [
            {
                "page_num": 1,
                "summary": "first 300 chars...",
                "headings": ["heading on this page"],
                "term_freq": {"word": 3, ...}
            },
            ...
        ],
        "inverted_index": {
            "word": [1, 5, 10, ...],
            ...
        }
    }

Terms are extracted with a simple tokenizer that handles English words
and Chinese characters (2-grams and 3-grams for Chinese to avoid jieba dependency).
"""

import json
import sys
import re
import math
import os
from collections import Counter, defaultdict

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


def tokenize(text):
    """Simple tokenizer for mixed Chinese/English text."""
    tokens = []
    text_lower = text.lower()
    for w in re.findall(r'[a-z0-9]+', text_lower):
        if len(w) > 1:
            tokens.append(w)
    for seq in re.findall(r'[\u4e00-\u9fff]+', text_lower):
        for ch in seq:
            tokens.append(ch)
        for i in range(len(seq) - 1):
            tokens.append(seq[i:i+2])
        for i in range(len(seq) - 2):
            tokens.append(seq[i:i+3])
    return tokens


def build_index_fitz(pdf_path, structure, use_ocr=False, ocr_engine="auto",
                     ocr_lang="eng", ocr_dpi=300, force_ocr=False):
    import fitz

    doc = fitz.open(pdf_path)
    pages_data = []
    inverted = defaultdict(set)
    idf = defaultdict(int)
    total_docs = len(doc)

    headings_map = defaultdict(list)
    for h in structure.get("toc", []):
        headings_map[h["page"]].append(h["title"])
    for h in structure.get("heuristic_headings", []):
        headings_map[h["page"]].append(h["title"])

    ocr_pages_count = 0
    for pnum in range(len(doc)):
        page = doc.load_page(pnum)
        text = extract_page_text(
            page, use_ocr=use_ocr, engine_name=ocr_engine,
            language=ocr_lang, dpi=ocr_dpi, force_ocr=force_ocr
        )
        if use_ocr and text != page.get_text():
            ocr_pages_count += 1
        summary = text[:500].replace("\n", " ")
        tokens = tokenize(text)
        tf = Counter(tokens)
        page_info = {
            "page_num": pnum + 1,
            "summary": summary,
            "headings": list(set(headings_map.get(pnum + 1, []))),
            "term_freq": dict(tf.most_common(100)),
            "char_count": len(text),
        }
        pages_data.append(page_info)
        for term in tf:
            inverted[term].add(pnum + 1)
            idf[term] += 1
    doc.close()

    inverted_index = {k: sorted(list(v)) for k, v in inverted.items()}
    idf_scores = {k: math.log((total_docs + 1) / (v + 1)) + 1 for k, v in idf.items()}
    result = {
        "source_pdf": pdf_path,
        "total_pages": total_docs,
        "pages": pages_data,
        "inverted_index": inverted_index,
        "idf": idf_scores,
    }
    if use_ocr:
        result["ocr_pages_count"] = ocr_pages_count
    return result


def build_index_pypdf(pdf_path, structure):
    import pypdf
    reader = pypdf.PdfReader(pdf_path)
    pages_data = []
    inverted = defaultdict(set)
    idf = defaultdict(int)
    total_docs = len(reader.pages)

    headings_map = defaultdict(list)
    for h in structure.get("toc", []):
        headings_map[h["page"]].append(h["title"])
    for h in structure.get("heuristic_headings", []):
        headings_map[h["page"]].append(h["title"])

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        summary = text[:500].replace("\n", " ")
        tokens = tokenize(text)
        tf = Counter(tokens)
        page_info = {
            "page_num": i + 1,
            "summary": summary,
            "headings": list(set(headings_map.get(i + 1, []))),
            "term_freq": dict(tf.most_common(100)),
            "char_count": len(text),
        }
        pages_data.append(page_info)
        for term in tf:
            inverted[term].add(i + 1)
            idf[term] += 1

    inverted_index = {k: sorted(list(v)) for k, v in inverted.items()}
    idf_scores = {k: math.log((total_docs + 1) / (v + 1)) + 1 for k, v in idf.items()}
    return {
        "source_pdf": pdf_path,
        "total_pages": total_docs,
        "pages": pages_data,
        "inverted_index": inverted_index,
        "idf": idf_scores,
    }


def parse_args(argv):
    args = {
        "pdf_path": None,
        "struct_path": None,
        "out_path": None,
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
        if a == "--ocr":
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
            elif args["struct_path"] is None:
                args["struct_path"] = a
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

    if not args["pdf_path"] or not args["struct_path"]:
        print(__doc__)
        sys.exit(1)

    out_path = args["out_path"] if args["out_path"] else args["pdf_path"].rsplit(".", 1)[0] + "_index.json"

    with open(args["struct_path"], "r", encoding="utf-8") as f:
        structure = json.load(f)

    backend = check_deps()
    if backend == "fitz":
        index = build_index_fitz(
            args["pdf_path"], structure,
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
        index = build_index_pypdf(args["pdf_path"], structure)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Index built: {out_path}")
    print(f"  Pages indexed: {index['total_pages']}")
    print(f"  Unique terms: {len(index['inverted_index'])}")
    if "ocr_pages_count" in index:
        print(f"  OCR pages: {index['ocr_pages_count']}")


if __name__ == "__main__":
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
