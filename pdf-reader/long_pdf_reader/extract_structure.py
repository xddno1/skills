#!/usr/bin/env python3
"""
Extract table of contents and heading structure from a PDF.

Usage:
    python -m long_pdf_reader.extract_structure <input.pdf> [output.json]

Output JSON format:
    {
        "source_pdf": "path/to/file.pdf",
        "total_pages": 300,
        "metadata": {...},
        "toc": [
            {"level": 1, "title": "Chapter 1", "page": 1},
            ...
        ],
        "heuristic_headings": [
            {"level": 1, "title": "1.1 Introduction", "page": 5, "y": 100.5},
            ...
        ]
    }
"""

import json
import sys
import re


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
    print("  pip install pymupdf      # recommended, fastest")
    print("  pip install pypdf        # pure-python fallback")
    sys.exit(1)


def extract_with_fitz(path):
    import fitz
    doc = fitz.open(path)
    result = {
        "source_pdf": path,
        "total_pages": len(doc),
        "metadata": dict(doc.metadata),
        "toc": [],
        "heuristic_headings": [],
    }

    # Embedded TOC / outline
    toc = doc.get_toc()
    for item in toc:
        level, title, page = item[0], item[1], item[2]
        # page in get_toc() is 1-based
        result["toc"].append({
            "level": level,
            "title": title.strip(),
            "page": page,
        })

    # Heuristic heading extraction (font-size based)
    # We sample first ~20 pages to find heading font size thresholds
    font_sizes = []
    sample_pages = min(20, len(doc))
    for pnum in range(sample_pages):
        page = doc.load_page(pnum)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    txt = span["text"].strip()
                    if len(txt) > 3 and len(txt) < 200:
                        font_sizes.append((span["size"], txt, pnum, span["origin"][1]))

    if font_sizes:
        sizes = [s for s, _, _, _ in font_sizes]
        sizes.sort(reverse=True)
        # Use top 5% font sizes as headings
        cutoff_idx = max(1, len(sizes) // 20)
        cutoff = sizes[min(cutoff_idx, len(sizes) - 1)]

        headings = []
        for size, txt, pnum, y in font_sizes:
            if size >= cutoff and not re.match(r"^\d+$", txt):
                # Determine level by relative size
                if size >= cutoff + 2:
                    level = 1
                elif size >= cutoff + 1:
                    level = 2
                else:
                    level = 3
                headings.append({
                    "level": level,
                    "title": txt,
                    "page": pnum + 1,
                    "y": round(y, 2),
                })

        # Deduplicate / sort
        seen = set()
        unique = []
        for h in sorted(headings, key=lambda x: (x["page"], x["y"])):
            key = (h["page"], h["title"])
            if key not in seen:
                seen.add(key)
                unique.append(h)
        result["heuristic_headings"] = unique[:200]  # limit

    doc.close()
    return result


def extract_with_pypdf(path):
    import pypdf
    reader = pypdf.PdfReader(path)
    result = {
        "source_pdf": path,
        "total_pages": len(reader.pages),
        "metadata": dict(reader.metadata or {}),
        "toc": [],
        "heuristic_headings": [],
    }
    # pypdf cannot do heuristic heading extraction easily
    # Just extract first line of each page as a guess
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines and len(lines[0]) < 150:
            result["heuristic_headings"].append({
                "level": 2,
                "title": lines[0],
                "page": i + 1,
                "y": 0,
            })
    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else pdf_path.rsplit(".", 1)[0] + "_structure.json"

    backend = check_deps()
    if backend == "fitz":
        data = extract_with_fitz(pdf_path)
    else:
        data = extract_with_pypdf(pdf_path)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Structure extracted to: {out_path}")
    print(f"  Total pages: {data['total_pages']}")
    print(f"  TOC entries: {len(data['toc'])}")
    print(f"  Heuristic headings: {len(data['heuristic_headings'])}")


if __name__ == "__main__":
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
