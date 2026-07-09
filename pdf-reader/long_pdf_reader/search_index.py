#!/usr/bin/env python3
"""
Search a PDF index and return the most relevant page numbers.

Usage:
    python -m long_pdf_reader.search_index <index.json> "query string" [--top N] [--format concise|detailed]

Output (concise):
    [10, 45, 78]

Output (detailed, default):
    [
      {"page": 10, "score": 0.85, "summary": "...", "headings": [...]},
      ...
    ]

Scoring uses a simple TF-IDF variant combined with heading matches.
"""

import json
import sys
import re
import math
import argparse
from collections import Counter


def tokenize(text):
    text_lower = text.lower()
    tokens = []
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


def search(index_data, query, top_k=10):
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    inv = index_data.get("inverted_index", {})
    idf = index_data.get("idf", {})
    pages = index_data.get("pages", [])
    total_pages = index_data.get("total_pages", 1)

    scores = Counter()
    heading_hits = Counter()

    # Score by inverted index presence + TF-IDF weighting
    for term in query_tokens:
        matched_pages = inv.get(term, [])
        idf_weight = idf.get(term, math.log(total_pages + 1))
        for pnum in matched_pages:
            scores[pnum] += idf_weight

    # Boost pages where query tokens appear in headings
    for p in pages:
        pnum = p["page_num"]
        heading_text = " ".join(p.get("headings", [])).lower()
        for term in query_tokens:
            if term in heading_text:
                heading_hits[pnum] += 1
                scores[pnum] += idf.get(term, 1) * 3.0  # heading boost

    # Normalize by page length (char_count) to avoid bias toward long pages
    for p in pages:
        pnum = p["page_num"]
        char_count = p.get("char_count", 1)
        if char_count > 0:
            scores[pnum] = scores[pnum] / math.sqrt(char_count)

    # Get top results
    top = scores.most_common(top_k)
    results = []
    for pnum, score in top:
        page_info = next((p for p in pages if p["page_num"] == pnum), None)
        if page_info:
            results.append({
                "page": pnum,
                "score": round(score, 4),
                "summary": page_info.get("summary", ""),
                "headings": page_info.get("headings", []),
                "heading_match": heading_hits[pnum] > 0,
            })
    return results


def parse_range(spec):
    """Expand a page range spec like '10-20,25,30-35' into a sorted list."""
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a), int(b) + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


def main():
    parser = argparse.ArgumentParser(description="Search PDF index")
    parser.add_argument("index", help="Path to index.json")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top", type=int, default=10, help="Number of top results")
    parser.add_argument("--format", choices=["concise", "detailed"], default="detailed")
    parser.add_argument("--expand", type=int, default=0, help="Expand each result by N pages on each side")
    args = parser.parse_args()

    with open(args.index, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    results = search(index_data, args.query, top_k=args.top)

    if args.format == "concise":
        out = []
        for r in results:
            if args.expand > 0:
                start = max(1, r["page"] - args.expand)
                end = min(index_data["total_pages"], r["page"] + args.expand)
                out.append(f"{start}-{end}")
            else:
                out.append(r["page"])
        print(json.dumps(out, ensure_ascii=False))
    else:
        if args.expand > 0:
            for r in results:
                start = max(1, r["page"] - args.expand)
                end = min(index_data["total_pages"], r["page"] + args.expand)
                r["expanded_range"] = f"{start}-{end}"
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys
    import io
    # Fix Windows console encoding issues
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
