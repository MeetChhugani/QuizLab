import fitz  # pymupdf
import pdfplumber
import traceback

def extract_text_from_pdf(uploaded_file):
    """
    Attempts to extract text from an uploaded PDF stream.
    Tries PyMuPDF (fitz) first, falling back to pdfplumber if needed.
    Returns (extracted_text, error_logs).
    """
    text = ""
    error_logs = []

    # 1. Try PyMuPDF (fitz)
    try:
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
    except Exception as e:
        tb = traceback.format_exc()
        error_logs.append(f"PyMuPDF Exception: {e}\n{tb}")

    # 2. Try pdfplumber as a fallback if PyMuPDF failed or extracted too little text
    if len(text.strip()) < 100:
        try:
            uploaded_file.seek(0)
            with pdfplumber.open(uploaded_file) as pdf:
                plumber_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        plumber_text += page_text + "\n"
                
                # If pdfplumber extracted more text, use it
                if len(plumber_text.strip()) >= len(text.strip()):
                    text = plumber_text
        except Exception as e:
            tb = traceback.format_exc()
            error_logs.append(f"pdfplumber Fallback Exception: {e}\n{tb}")

    return text, error_logs
