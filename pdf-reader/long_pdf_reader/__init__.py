"""
long-pdf-reader

Read, search, and precisely locate content in very long PDF documents
such as textbooks, manuals, and large reports.
"""

__version__ = "0.1.0"

from .ocr_utils import (
    OCREngine,
    OCRError,
    PyMuPDFOCR,
    PyTesseractOCR,
    EasyOCROCR,
    get_ocr_engine,
    extract_page_text,
    is_scan_page,
    ocr_engine_info,
)

__all__ = [
    "OCREngine",
    "OCRError",
    "PyMuPDFOCR",
    "PyTesseractOCR",
    "EasyOCROCR",
    "get_ocr_engine",
    "extract_page_text",
    "is_scan_page",
    "ocr_engine_info",
]
