# Long PDF Reader

Read, search, and precisely locate content in very long PDF documents such as textbooks, manuals, and large reports.

## Features

- **Index-based search** — Never load the entire PDF into memory/context. Build an inverted index once, search in milliseconds.
- **Text-layer & OCR support** — Works with native text PDFs and scanned/image-only PDFs via multiple OCR backends.
- **Structure extraction** — Automatically extracts TOC and detects headings from font size heuristics.
- **Searchable PDF conversion** — Convert scanned PDFs into standard searchable PDFs with an invisible OCR text layer.
- **Chinese & English** — Tokenizer handles mixed CJK / Latin text out of the box.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/long-pdf-reader.git
cd long-pdf-reader

# Install the package
pip install -e .

# Recommended: install PyMuPDF for best performance and heading detection
pip install pymupdf

# Optional: install OCR backends as needed
pip install pytesseract pillow   # if you have Tesseract installed
pip install easyocr              # no Tesseract required
```

## Quick Start

### 1. Extract Structure

```bash
lpdf-extract-structure textbook.pdf textbook_structure.json
```

### 2. Build Search Index

```bash
lpdf-build-index textbook.pdf textbook_structure.json textbook_index.json
```

For scanned PDFs, add `--ocr`:

```bash
lpdf-build-index scan.pdf structure.json index.json --ocr --ocr-lang ch_sim
```

### 3. Search

```bash
lpdf-search-index textbook_index.json "machine learning" --top 5 --expand 1
```

### 4. Extract Pages

```bash
lpdf-extract-pages textbook.pdf "45-47,120-122" extracted.txt
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `lpdf-extract-structure` | Extract TOC and heading structure from a PDF |
| `lpdf-build-index` | Build a full-text inverted index |
| `lpdf-search-index` | Search the index for relevant pages |
| `lpdf-extract-pages` | Extract text from specific page ranges |
| `lpdf-ocr-to-searchable` | Convert scanned PDFs to searchable PDFs |
| `lpdf-ocr-info` | Show available OCR engines |

You can also run the scripts directly without installing:

```bash
python scripts/extract_structure.py textbook.pdf structure.json
python scripts/build_index.py textbook.pdf structure.json index.json
python scripts/search_index.py index.json "query" --top 5
python scripts/extract_pages.py textbook.pdf "10-20" out.txt
```

## OCR Backends

| Engine | Install | Needs Tesseract | Speed | Best For |
|--------|---------|-----------------|-------|----------|
| **PyMuPDF built-in** | `pip install pymupdf` | Yes | Fastest | General use |
| **pytesseract** | `pip install pytesseract pillow` | Yes | Medium | Fine-grained bbox control |
| **EasyOCR** | `pip install easyocr` | **No** | Medium | No system deps; CJK support |

Check what your system supports:

```bash
lpdf-ocr-info
```

## Converting Scans to Searchable PDFs

If you query a scanned PDF repeatedly, convert it once:

```bash
lpdf-ocr-to-searchable old_scan.pdf new_searchable.pdf --ocr-lang ch_sim
```

Then index the output normally without `--ocr`.

## Python API

```python
from long_pdf_reader import get_ocr_engine, extract_page_text
import fitz

doc = fitz.open("scan.pdf")
page = doc.load_page(0)

# Extract with auto OCR
text = extract_page_text(page, use_ocr=True, engine_name="auto", language="eng")
print(text)
```

## Dependencies

- Python 3.8+
- `pymupdf` (recommended) or `pypdf` (fallback)
- Optional OCR: `pytesseract`, `Pillow`, `easyocr`

## License

MIT
