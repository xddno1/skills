#!/usr/bin/env python3
"""
Convert a scanned (image-only) PDF into a Searchable PDF.

Usage:
    python scripts/ocr_to_searchable_pdf.py <input.pdf> <output.pdf>
"""

import sys
import os

# Allow running directly from repo without pip install
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from long_pdf_reader.ocr_to_searchable_pdf import main

if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
