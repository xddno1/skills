# Long PDF Reader Workflow

## Overview

This skill enables precise content location and reading in very long PDFs
(textbooks, manuals, research papers) that exceed the context window.

It supports both **text-layer PDFs** (fast, no extra deps) and **scanned/image-only PDFs**
(via OCR with multiple backend options).

## Core Principle

**Never load the entire PDF into context.**
Instead: index -> search -> extract relevant pages -> answer.

---

## Step-by-Step Workflow

### 1. Prerequisites Check

Ensure the user has a PDF library installed:

```bash
pip install pymupdf   # recommended, fastest, best heading detection
# OR
pip install pypdf     # pure-python fallback
```

If working with scanned PDFs, also set up OCR. Check what is available:

```bash
python scripts/ocr_utils.py
```

### 2. Extract Structure (one-time per PDF)

```bash
python scripts/extract_structure.py textbook.pdf textbook_structure.json
```

This produces:
- `toc`: embedded table of contents (if present)
- `heuristic_headings`: font-size-based heading detection (PyMuPDF only)
- `total_pages`

### 3. Build Search Index (one-time per PDF)

**For normal PDFs:**
```bash
python scripts/build_index.py textbook.pdf textbook_structure.json textbook_index.json
```

**For scanned PDFs:**
```bash
python scripts/build_index.py scan.pdf textbook_structure.json scan_index.json --ocr --ocr-lang ch_sim
```

This produces an inverted index for fast keyword search. The `--ocr` flag automatically
OCRs only the image-only pages; pages with existing text are left as-is.

### 4. Answer User Questions

For each user query:

#### 4a. Search the Index

```bash
python scripts/search_index.py textbook_index.json "user query" --top 5 --expand 1
```

- `--top 5`: return top 5 most relevant pages
- `--expand 1`: include 1 page before/after for context

Output gives page ranges like `45-47`, `120-122`.

#### 4b. Extract Relevant Pages

**Normal PDF:**
```bash
python scripts/extract_pages.py textbook.pdf "45-47,120-122" extracted.txt
```

**Scanned PDF:**
```bash
python scripts/extract_pages.py scan.pdf "45-47,120-122" extracted.txt --ocr --ocr-lang ch_sim
```

#### 4c. Read Extracted Text and Answer

Load `extracted.txt` into context, cite page numbers, and answer.

---

## Converting Scans to Searchable PDFs (Permanent Fix)

If you will query a scanned PDF many times, convert it once to a **Searchable PDF**
so you never need `--ocr` again:

```bash
python scripts/ocr_to_searchable_pdf.py old_scan.pdf new_searchable.pdf --ocr-lang ch_sim
```

Then build the index from `new_searchable.pdf` without `--ocr`:

```bash
python scripts/build_index.py new_searchable.pdf structure.json index.json
```

### Why this is better for repeated use

- **One-time cost**: OCR runs once during conversion, not on every query.
- **Full compatibility**: The output is a standard PDF readable by any viewer.
- **Persistent text layer**: The invisible text is embedded inside the PDF; no external files needed.
- **Preserved visuals**: Original scan images remain untouched; text is invisible (`render_mode=3`).

---

## Direct Page Navigation

If the user asks about a specific chapter or page:

- Use `structure.json` to map chapter titles -> page numbers
- Then `extract_pages.py` to pull that range

---

## OCR Engine Guide

| Situation | Recommended Engine | Install |
|-----------|-------------------|---------|
| Tesseract already on PATH | `pymupdf` (auto) | nothing extra |
| Need fine bbox control | `pytesseract` | `pip install pytesseract pillow` |
| Cannot install Tesseract | `easyocr` | `pip install easyocr` |
| Mixed Chinese/English scans | `easyocr` | `pip install easyocr` (lang `ch_sim,en`) |

Specify engine explicitly:
```bash
python scripts/extract_pages.py scan.pdf "1-10" out.txt --ocr --ocr-engine easyocr --ocr-lang ch_sim,en
```

---

## Index File Size Management

For very large PDFs (1000+ pages):

- `index.json` can grow to 20-50 MB.
- Search is still fast (pure JSON in-memory).
- If memory is a concern, split index by chapters after building.

---

## Accuracy Tips

1. **Heading boost**: search scores pages higher when query terms appear in headings.
2. **Expand range**: always use `--expand 1` or `--expand 2` to catch context.
3. **Multi-pass search**: if first results are poor, rephrase query and search again.
4. **Verify with structure**: cross-check `toc` entries before extracting.
5. **OCR language**: always set `--ocr-lang` correctly; wrong language = garbled text.
6. **DPI**: default 300 is good for most scans. For very small text, try `--ocr-dpi 400`.
