# LegalDoc Guardian

**LegalDoc Guardian** — a lightweight document forgery detection demo that extracts fields from scanned/photographed payment slips and detects suspicious edits (such as duplicated or inconsistent amounts). Built as a Streamlit demo with a local OCR + rule-based detector and a fallback OCR pipeline.

**Live demo (cloud-friendly):** _Paste your Streamlit URL here after deployment._  
**Source code:** https://github.com/SRIKRISH-S/legaldoc-guardian

---

## Why this project
Financial document forgery (edited amounts, replaced account numbers) causes large financial loss. This project helps detect suspicious edits quickly and produces explainable evidence (highlighted boxes + JSON) for investigators.

---

## Features
- Upload a document image (photo or scan) and get a fast forgery check.  
- Multi-engine OCR pipeline: PaddleOCR (preferred) → Tesseract (fallback).  
- Image enhancement (deskew, denoise, contrast, adaptive threshold) to improve OCR from mobile photos.  
- Field extraction: name, account, amount(s), date, signature area.  
- Forgery detector: rule-based evidence (multiple amounts, missing account) + simple ML fallback.  
- Demo mode for cloud deployments (precomputed examples) + full local pipeline support.  
- Export results as JSON for audit/evidence.

---

## Quick Start (local)
Requirements: Python 3.10+, recommended in a virtualenv.

```bash
# create venv (if not already)
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# (Optional) For full OCR locally install PaddleOCR / paddlepaddle and Tesseract:
# pip install paddleocr
# Install tesseract binary (Windows: UB Mannheim build; Linux: apt install tesseract-ocr)
# pip install pytesseract

streamlit run src/webapp/app.py
