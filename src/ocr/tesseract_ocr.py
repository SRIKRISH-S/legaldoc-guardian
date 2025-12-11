# src/ocr/tesseract_ocr.py
"""
Tesseract OCR wrapper.

Provides:
- tesseract_ocr(image_path) -> list of {"box": [[x,y],...], "text": str, "conf": float}
- draw_boxes(image_path, ocr_list, out_path="tess_boxes.png")
This module is defensive: if pytesseract / cv2 are not available, functions return empty lists
(or raise only at call-time with friendly messages).
"""

import os
import json

def _safe_imports():
    pytesseract = None
    cv2 = None
    Image = None
    try:
        import pytesseract as _p
        # set default windows path automatically if exists
        default_windows = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_windows):
            try:
                _p.pytesseract.tesseract_cmd = default_windows
            except Exception:
                pass
        pytesseract = _p
    except Exception:
        pytesseract = None
    try:
        import cv2 as _cv
        cv2 = _cv
    except Exception:
        cv2 = None
    try:
        from PIL import Image as _Image
        Image = _Image
    except Exception:
        Image = None
    return pytesseract, cv2, Image

def tesseract_ocr(image_path):
    pytesseract, cv2, Image = _safe_imports()
    if pytesseract is None or Image is None:
        print("tesseract_ocr: pytesseract or Pillow not available in environment.")
        return []

    try:
        pil_img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print("tesseract_ocr: Failed to open image:", e)
        return []

    try:
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    except Exception as e:
        print("tesseract_ocr: pytesseract.image_to_data failed:", e)
        return []

    results = []
    n = len(data.get("text", []))
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if txt == "":
            continue
        try:
            left = int(data["left"][i]); top = int(data["top"][i])
            width = int(data["width"][i]); height = int(data["height"][i])
        except Exception:
            try:
                left = int(float(data["left"][i])); top = int(float(data["top"][i]))
                width = int(float(data["width"][i])); height = int(float(data["height"][i]))
            except Exception:
                continue
        conf_raw = data.get("conf", [])[i] if "conf" in data else -1
        try:
            conf = float(conf_raw) if conf_raw is not None and conf_raw != '' else 0.0
        except Exception:
            conf = 0.0

        x1, y1 = left, top
        x2, y2 = left + width, top
        x3, y3 = left + width, top + height
        x4, y4 = left, top + height
        box = [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]

        results.append({"box": box, "text": txt, "conf": conf})
    return results

def draw_boxes(image_path, ocr_list, out_path="tess_boxes.png"):
    _, _, Image = _safe_imports()
    if Image is None:
        raise RuntimeError("Pillow not available; cannot draw boxes.")
    try:
        from PIL import ImageDraw, ImageFont
    except Exception:
        ImageDraw = None
        ImageFont = None

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = None

    for it in ocr_list:
        box = it.get("box") or []
        txt = it.get("text", "")
        if not box:
            continue
        try:
            pts = [tuple(map(int, p)) for p in box]
        except Exception:
            continue
        draw.line(pts + [pts[0]], width=2, fill=(0, 255, 0))
        if font:
            try:
                draw.text((pts[0][0], max(0, pts[0][1]-18)), txt[:30], fill=(0,255,0), font=font)
            except Exception:
                draw.text((pts[0][0], max(0, pts[0][1]-18)), txt[:30], fill=(0,255,0))
    img.save(out_path)
    return out_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tesseract_ocr.py <image_path>")
        sys.exit(0)
    imgp = sys.argv[1]
    res = tesseract_ocr(imgp)
    print(json.dumps(res[:30], indent=2, ensure_ascii=False))
