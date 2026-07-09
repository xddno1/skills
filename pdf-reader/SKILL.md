---
name: long-pdf-reader
description: Read, search, and precisely locate content in very long PDF documents such as textbooks, manuals, and large reports. Use when the user needs to (1) find specific information in a multi-hundred-page PDF, (2) answer questions that require pinpointing chapter/section/page references, (3) extract and analyze content from specific page ranges without loading the entire file into context, (4) build a reusable search index for a large PDF, or (5) convert scanned/image-only PDFs into searchable text-layer PDFs.
---

# Long PDF Reader

Enable precise reading and content location in PDFs too large to fit in context.

**Two modes supported:**
- **Text-layer mode** (default): Fast extraction for PDFs that already contain text.
- **OCR mode**: Automatic or on-demand OCR for scanned/image-only PDFs.

---

## Dependencies

- `pymupdf` (recommended) or `pypdf` (fallback)
- Python 3.8+

Install: `pip install pymupdf`

### OCR Dependencies (optional)

OCR is only needed for scanned PDFs. Choose one backend:

| Engine | Install | Needs Tesseract (system) | Speed | Best for |
|--------|---------|--------------------------|-------|----------|
| **PyMuPDF built-in** | `pip install pymupdf` | Yes | Fastest | General use if Tesseract installed |
| **pytesseract** | `pip install pytesseract pillow` | Yes | Medium | Fine-grained control |
| **EasyOCR** | `pip install easyocr` | **No** | Medium | No system deps; downloads models on first run |

**Tesseract (Windows):** https://github.com/UB-Mannheim/tesseract/wiki

Check what your system supports:
```bash
python scripts/ocr_utils.py
```

---

## One-Time Setup Per PDF

Run these once for each PDF you want to query repeatedly:

```bash
python scripts/extract_structure.py <book.pdf> <book_structure.json>
python scripts/build_index.py <book.pdf> <book_structure.json> <book_index.json>
```

For **scanned PDFs**, add `--ocr` to the build step so image pages are OCR'd before indexing:

```bash
python scripts/build_index.py <scan.pdf> <structure.json> <index.json> --ocr --ocr-lang ch_sim
```

---

## Workflow for Answering Questions

For each user query about the PDF:

1. **Search**: Find relevant pages
   ```bash
   python scripts/search_index.py <book_index.json> "QUERY" --top 5 --expand 1
   ```
2. **Extract**: Pull only those pages
   ```bash
   python scripts/extract_pages.py <book.pdf> "RANGE" extracted.txt
   ```
3. **Answer**: Read `extracted.txt`, cite page numbers, respond.

If the user names a specific chapter or section, use `book_structure.json`
to map the title to a page range, then extract directly.

### For Scanned PDFs

When extracting pages from a scanned book, add `--ocr` so scan pages are read via OCR:

```bash
python scripts/extract_pages.py <scan.pdf> "45-47" extracted.txt --ocr --ocr-lang ch_sim
```

---

## Convert Scanned PDF to Searchable PDF

Create a new PDF that keeps the original scan images but adds an invisible OCR text layer on top. This makes the PDF permanently searchable, copyable, and compatible with standard PDF readers.

```bash
python scripts/ocr_to_searchable_pdf.py <input_scan.pdf> <output_searchable.pdf> --ocr-lang ch_sim
```

Options:
- `--force-ocr` — OCR every page even if a text layer already exists
- `--pages 1-20,50` — process only specific pages
- `--ocr-engine easyocr` — use a specific OCR backend

After conversion, you can index the output PDF with the normal `build_index.py` (no `--ocr` needed because it now has a text layer).

---

## Scripts

- `scripts/extract_structure.py` — Extract TOC and heading structure
- `scripts/build_index.py` — Build full-text inverted index (add `--ocr` for scans)
- `scripts/search_index.py` — Search index for relevant pages
- `scripts/extract_pages.py` — Extract text from specific page ranges (add `--ocr` for scans)
- `scripts/ocr_to_searchable_pdf.py` — Convert scan PDFs to searchable PDFs with invisible text layer
- `scripts/ocr_utils.py` — Shared OCR backend abstraction and engine detection

---

## Advanced Usage

- Use `--format concise` in `search_index.py` to get just page numbers.
- Use `--expand N` to include N pages of surrounding context.
- Use `--force-ocr` if you suspect the existing text layer is poor quality.
- See `references/workflow.md` for detailed patterns and troubleshooting.
