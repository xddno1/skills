#!/usr/bin/env python3
"""
OCR utilities for long-pdf-reader.

Usage:
    python scripts/ocr_utils.py
"""

import sys
import os

# Allow running directly from repo without pip install
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from long_pdf_reader.ocr_utils import ocr_engine_info

if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print(ocr_engine_info())
