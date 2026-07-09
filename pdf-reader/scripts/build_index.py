#!/usr/bin/env python3
"""
Build a searchable index from a PDF and its structure file.

Usage:
    python scripts/build_index.py <input.pdf> <structure.json> [output.json]
"""

import sys
import os

# Allow running directly from repo without pip install
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from long_pdf_reader.build_index import main

if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
