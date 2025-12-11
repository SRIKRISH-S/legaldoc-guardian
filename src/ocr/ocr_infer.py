# src/ocr/ocr_infer.py
"""
Wrapper for PaddleOCR. Defensive: if paddleocr is not installed, functions return empty list.
Provides:
- ocr_image(image_path) -> list of {"box": [[x,y],...], "text": str, "conf": float}
- draw_boxes(image_path, ocr_list, out_path="ocr_boxes.png")
"""
import os, json

def _safe_imports():
    try:
        from paddleocr import PaddleOCR
        return PaddleOCR
    except Exception as e:
        print("paddleocr not available:", repr(e))
        return None

PaddleOCR = _safe_imports()

def ocr_image(image_path):
    """
    If PaddleOCR available, run it. Otherwise return [].
    """
    if PaddleOCR is None:
        return []
    try:
        ocr = PaddleOCR(use_textline_orientation=True, lang='en')
        # predict returns list of lines; convert to uniform format
        result = ocr.ocr(image_path, cls=True) if hasattr(ocr, "ocr") else ocr.predict(image_path)
        # normalize to list of dicts with box/text/conf
        out = []
        for line in result:
            # expected line formats differ; handle generically
            try:
                box = line[0]
                text = line[1][0] if isinstance(line[1], (list,tuple)) else (line[1].get("text") if isinstance(line[1], dict) else str(line[1]))
                conf = float(line[1][1]) if isinstance(line[1], (list,tuple)) and len(line[1])>1 else 0.0
            except Exception:
                # fallback: if line is dict already
                box = line.get("box", [])
                text = line.get("text", "")
                conf = line.get("conf", 0.0)
            out.append({"box": box, "text": text, "conf": conf})
        return out
    except Exception as e:
        print("PaddleOCR run failed:", repr(e))
        return []

def draw_boxes(image_path, ocr_list, out_path="ocr_boxes.png"):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        raise RuntimeError("Pillow not installed; cannot draw boxes")
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for it in ocr_list:
        box = it.get("box") or []
        txt = it.get("text","")
        if not box:
            continue
        try:
            pts = [tuple(map(int,p)) for p in box]
        except Exception:
            continue
        draw.line(pts + [pts[0]], width=2, fill=(0,255,0))
        draw.text((pts[0][0], max(0, pts[0][1]-18)), txt[:30], fill=(0,255,0))
    img.save(out_path)
    return out_path
