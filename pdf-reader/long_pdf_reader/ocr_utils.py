#!/usr/bin/env python3
"""
OCR utilities for long-pdf-reader.
Supports multiple OCR backends with automatic detection and fallback.
"""

import sys
import io
import shutil
from typing import List, Tuple, Optional


class OCRError(Exception):
    """Raised when OCR is requested but unavailable or fails."""
    pass


def get_text_density(text: str) -> float:
    """Calculate text density to detect scan pages."""
    if not text:
        return 0.0
    meaningful = sum(1 for c in text if c.isalnum() or "\u4e00" <= c <= "\u9fff")
    return meaningful / len(text)


def is_scan_page(page, threshold: float = 0.05, min_chars: int = 30) -> bool:
    """
    Heuristic to detect if a page is image-only (scan).

    Returns True if the page has very little or no extractable text.
    """
    text = page.get_text()
    if len(text) < min_chars:
        return True
    density = get_text_density(text)
    return density < threshold


def check_tesseract_installed() -> bool:
    """Check if Tesseract OCR binary is available on system PATH."""
    return shutil.which("tesseract") is not None


def ocr_engine_info() -> str:
    """Return a human-readable summary of available OCR options."""
    has_tess = check_tesseract_installed()
    lines = [
        "OCR engine status:",
        f"  - Tesseract (system): {'available' if has_tess else 'NOT FOUND'}",
    ]
    for name, desc in [
        ("pymupdf", "PyMuPDF built-in OCR (fastest, needs Tesseract)"),
        ("pytesseract", "pytesseract wrapper (needs Tesseract + pip install pytesseract pillow)"),
        ("easyocr", "EasyOCR (no Tesseract needed, pip install easyocr)"),
    ]:
        lines.append(f"  - {name}: {desc}")
    return "\n".join(lines)


class OCREngine:
    """Abstract base for OCR backends."""

    name = "base"

    def extract_text(self, page, dpi: int = 300) -> str:
        raise NotImplementedError

    def extract_blocks(self, page, dpi: int = 300) -> List[Tuple[str, Tuple[float, float, float, float]]]:
        """
        Extract text blocks with bounding boxes.
        Returns list of (text, (x0, y0, x1, y1)) in PDF page coordinates.
        """
        # Default implementation: no bbox info
        text = self.extract_text(page, dpi=dpi)
        return [(text, (0, 0, page.rect.width, page.rect.height))]


class PyMuPDFOCR(OCREngine):
    """PyMuPDF built-in OCR (fastest; requires Tesseract on system PATH)."""

    name = "pymupdf"

    def __init__(self, language: str = "eng"):
        self.language = language
        try:
            import fitz
            doc = fitz.open()
            p = doc.new_page()
            p.get_textpage_ocr(flags=0, language=language)
            doc.close()
        except RuntimeError as e:
            err = str(e)
            if "Tesseract" in err or "tessdata" in err:
                raise OCRError(
                    "PyMuPDF OCR requires Tesseract installed on the system.\n"
                    "Windows installer: https://github.com/UB-Mannheim/tesseract/wiki\n"
                    "After install, ensure 'tesseract' is on your PATH."
                )
            raise OCRError(f"PyMuPDF OCR init failed: {err}")

    def extract_text(self, page, dpi: int = 300) -> str:
        tp = page.get_textpage_ocr(flags=0, language=self.language, dpi=dpi)
        return tp.extractText()


class PyTesseractOCR(OCREngine):
    """OCR via pytesseract + Pillow."""

    name = "pytesseract"

    def __init__(self, language: str = "eng"):
        try:
            import pytesseract
            self._pytesseract = pytesseract
            self.language = language
        except ImportError as e:
            raise OCRError(
                "pytesseract not installed. Run: pip install pytesseract pillow\n"
                "Also requires Tesseract system install: https://github.com/UB-Mannheim/tesseract/wiki"
            ) from e

    def _page_to_image(self, page, dpi: int):
        pix = page.get_pixmap(dpi=dpi)
        from PIL import Image
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    def extract_text(self, page, dpi: int = 300) -> str:
        img = self._page_to_image(page, dpi)
        return self._pytesseract.image_to_string(img, lang=self.language)

    def extract_blocks(self, page, dpi: int = 300):
        img = self._page_to_image(page, dpi)
        data = self._pytesseract.image_to_data(img, lang=self.language, output_type=self._pytesseract.Output.DICT)
        blocks = []
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            if not text:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            # Convert image coords to PDF page coords (approximate)
            rect = page.rect
            scale_x = rect.width / img.width
            scale_y = rect.height / img.height
            bbox = (x * scale_x, y * scale_y, (x + w) * scale_x, (y + h) * scale_y)
            blocks.append((text, bbox))
        return blocks


class EasyOCROCR(OCREngine):
    """OCR via EasyOCR (no Tesseract required; downloads models on first use)."""

    name = "easyocr"

    def __init__(self, language: Optional[List[str]] = None):
        try:
            import easyocr
            self.language = language or ["ch_sim", "en"]
            # EasyOCR Reader init can be slow; do it once
            self._reader = easyocr.Reader(self.language, gpu=False)
        except ImportError as e:
            raise OCRError(
                "easyocr not installed. Run: pip install easyocr\n"
                "First use will download OCR models automatically."
            ) from e

    def extract_text(self, page, dpi: int = 300) -> str:
        blocks = self.extract_blocks(page, dpi)
        return "\n".join(b[0] for b in blocks)

    def extract_blocks(self, page, dpi: int = 300):
        import numpy as np
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        results = self._reader.readtext(img, detail=1)
        blocks = []
        for r in results:
            # r format: (bbox, text, confidence)
            bbox_pts, text, conf = r
            # bbox_pts: [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
            xs = [p[0] for p in bbox_pts]
            ys = [p[1] for p in bbox_pts]
            # Scale from pixmap pixels to PDF page coords
            rect = page.rect
            scale_x = rect.width / pix.width
            scale_y = rect.height / pix.height
            pdf_bbox = (min(xs) * scale_x, min(ys) * scale_y, max(xs) * scale_x, max(ys) * scale_y)
            blocks.append((text, pdf_bbox))
        return blocks


ENGINES = {
    "pymupdf": PyMuPDFOCR,
    "pytesseract": PyTesseractOCR,
    "easyocr": EasyOCROCR,
}


def get_ocr_engine(engine_name: str = "auto", language: str = "eng") -> OCREngine:
    """
    Instantiate the requested OCR engine.

    Args:
        engine_name: 'auto', 'pymupdf', 'pytesseract', or 'easyocr'.
        language: OCR language code(s). For easyocr use list via comma, e.g. 'ch_sim,en'.

    Returns:
        An initialized OCREngine instance.

    Raises:
        OCRError: if the requested engine is unavailable.
    """
    if engine_name == "auto":
        # Preference: pymupdf (fastest) -> pytesseract -> easyocr
        for candidate in ("pymupdf", "pytesseract", "easyocr"):
            try:
                return get_ocr_engine(candidate, language)
            except OCRError:
                continue
        raise OCRError(
            "No OCR engine is available.\n\n"
            + ocr_engine_info()
            + "\n\nQuick start (no Tesseract needed):\n"
            "  pip install easyocr\n"
            "Then rerun with --ocr-engine easyocr"
        )

    if engine_name not in ENGINES:
        raise OCRError(f"Unknown OCR engine: {engine_name}. Choose from: auto, {', '.join(ENGINES.keys())}")

    cls = ENGINES[engine_name]
    if engine_name in ("pymupdf", "pytesseract") and not check_tesseract_installed():
        raise OCRError(
            f"Engine '{engine_name}' requires Tesseract on system PATH.\n"
            "Download: https://github.com/UB-Mannheim/tesseract/wiki"
        )

    # Language parsing
    if engine_name == "easyocr" and "," in language:
        langs = [l.strip() for l in language.split(",")]
        return cls(language=langs)
    return cls(language=language)


def ocr_engine_info_cli():
    """CLI entry point for lpdf-ocr-info."""
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print(ocr_engine_info())


def extract_page_text(page, use_ocr: bool = False, engine_name: str = "auto",
                      language: str = "eng", dpi: int = 300,
                      force_ocr: bool = False) -> str:
    """
    Extract text from a single PDF page.

    Args:
        page: fitz.Page instance.
        use_ocr: Whether OCR is enabled.
        engine_name: OCR backend to use.
        language: OCR language.
        dpi: Render DPI for OCR.
        force_ocr: If True, always OCR even if text layer exists.

    Returns:
        Extracted text string.
    """
    text = page.get_text()

    if not use_ocr:
        return text

    if not force_ocr and not is_scan_page(page):
        return text

    engine = get_ocr_engine(engine_name, language)
    return engine.extract_text(page, dpi=dpi)


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print(ocr_engine_info())
