#!/usr/bin/env python3
"""
Extract text from specific page ranges of a PDF.

Usage:
    python scripts/extract_pages.py <input.pdf> <page_spec> [output.txt]
"""

import sys
import os

# Allow running directly from repo without pip install
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from long_pdf_reader.extract_pages import main

if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
