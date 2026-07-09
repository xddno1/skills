#!/usr/bin/env python3
"""
Search a PDF index and return the most relevant page numbers.

Usage:
    python scripts/search_index.py <index.json> "query string" [--top N] [--format concise|detailed]
"""

import sys
import os

# Allow running directly from repo without pip install
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from long_pdf_reader.search_index import main

if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
