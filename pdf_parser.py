import fitz  # pymupdf
import pdfplumber
import traceback
import re
from io import BytesIO


def _ocr_pdf_pages(uploaded_file) -> tuple[list[dict], list[str]]:
    """Best-effort OCR for scanned PDFs when Tesseract is installed locally.

    OCR is deliberately optional: the application remains usable without a
    system Tesseract installation and reports an actionable extraction error.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return [], ["OCR is unavailable because pytesseract is not installed."]

    try:
        uploaded_file.seek(0)
        document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        pages = []
        for page_number, page in enumerate(document, start=1):
            # 200 DPI is a sensible balance between recognition quality and memory.
            pixmap = page.get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72), alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            text = pytesseract.image_to_string(image, config="--psm 3").strip()
            if text:
                pages.append(
                    {
                        "page_number": page_number,
                        "text": text,
                        "chapter": _infer_chapter_from_text(text),
                    }
                )
        return pages, []
    except Exception as exc:
        return [], [f"OCR failed: {exc}"]


def _infer_chapter_from_text(text: str) -> str:
    """Detect chapter/section headings from page text when reliably present."""
    for line in text.split("\n")[:8]:
        line = line.strip()
        if re.match(r"^(chapter|section|unit|module)\s+[\dIVXLC]+", line, re.I):
            return line[:120]
        if re.match(r"^\d+[\.\)]\s+[A-Z]", line):
            return line[:120]
    return ""


def extract_pages_from_pdf(uploaded_file) -> tuple[list[dict], list[str]]:
    """
    Extract text page-by-page with metadata for RAG indexing.
    Returns (pages, error_logs) where each page dict has:
      page_number (1-based), text, chapter (when detected).
    """
    pages: list[dict] = []
    error_logs: list[str] = []

    # 1. Try PyMuPDF (fitz) — preserves page boundaries
    try:
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for i, page in enumerate(doc, start=1):
            page_text = page.get_text() or ""
            if page_text.strip():
                pages.append(
                    {
                        "page_number": i,
                        "text": page_text,
                        "chapter": _infer_chapter_from_text(page_text),
                    }
                )
    except Exception as e:
        tb = traceback.format_exc()
        error_logs.append(f"PyMuPDF Exception: {e}\n{tb}")

    # 2. Fallback to pdfplumber if PyMuPDF failed or extracted too little
    total_chars = sum(len(p.get("text", "")) for p in pages)
    if total_chars < 100:
        try:
            uploaded_file.seek(0)
            plumber_pages = []
            with pdfplumber.open(uploaded_file) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        plumber_pages.append(
                            {
                                "page_number": i,
                                "text": page_text,
                                "chapter": _infer_chapter_from_text(page_text),
                            }
                        )
            plumber_chars = sum(len(p.get("text", "")) for p in plumber_pages)
            if plumber_chars >= total_chars:
                pages = plumber_pages
        except Exception as e:
            tb = traceback.format_exc()
            error_logs.append(f"pdfplumber Fallback Exception: {e}\n{tb}")

    # Scanned/image-only PDFs require OCR. Keep this as the final fallback so
    # normal text PDFs avoid the comparatively expensive rasterization step.
    total_chars = sum(len(p.get("text", "")) for p in pages)
    if total_chars < 100:
        ocr_pages, ocr_errors = _ocr_pdf_pages(uploaded_file)
        error_logs.extend(ocr_errors)
        if sum(len(p.get("text", "")) for p in ocr_pages) > total_chars:
            pages = ocr_pages

    return pages, error_logs


def extract_text_from_pdf(uploaded_file):
    """
    Attempts to extract text from an uploaded PDF stream.
    Tries PyMuPDF (fitz) first, falling back to pdfplumber if needed.
    Returns (extracted_text, error_logs).
    """
    pages, error_logs = extract_pages_from_pdf(uploaded_file)
    text = "\n".join(p.get("text", "") for p in pages)
    return text, error_logs

def extract_pages_from_file(uploaded_file) -> tuple[list[dict], list[str]]:
    """
    Extract page-level content from PDF, TXT, or MD uploads.
    Returns (pages, error_logs).
    """
    name = getattr(uploaded_file, "name", "").lower()
    if name.endswith((".txt", ".md")):
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            return [{"page_number": 1, "text": content, "chapter": ""}], []
        except Exception as e:
            tb = traceback.format_exc()
            return [], [f"Text/Markdown extraction exception: {e}\n{tb}"]
    return extract_pages_from_pdf(uploaded_file)


def extract_text_from_file(uploaded_file):
    """
    Extracts text from an uploaded file (PDF, TXT, or MD).
    Returns (extracted_text, error_logs).
    """
    pages, error_logs = extract_pages_from_file(uploaded_file)
    text = "\n".join(p.get("text", "") for p in pages)
    return text, error_logs
