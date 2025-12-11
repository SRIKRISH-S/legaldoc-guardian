# src/webapp/app.py
import sys, os, json
sys.path.append(os.path.abspath("."))

import streamlit as st
from PIL import Image

# Try to import OCR/detector lazily; if import fails, run in DEMO_MODE.
DEMO_MODE = False
ocr_image = None
tesseract_ocr = None
predict = None
draw_boxes_fn = None
extract_fields_from_ocr = None

try:
    # Import local wrappers if available
    from src.ocr.ocr_infer import ocr_image, draw_boxes as draw_boxes_paddle
    from src.ocr.tesseract_ocr import tesseract_ocr
    from src.forgery.forgery_detector import predict, extract_fields_from_ocr
    draw_boxes_fn = draw_boxes_paddle
except Exception as e:
    DEMO_MODE = True
    print("DEMO_MODE ON - heavy OCR modules not available:", repr(e))

st.set_page_config(page_title="LegalDoc Guardian", layout="wide")
st.title("LegalDoc Guardian — Demo (Cloud-friendly)")

st.markdown(
    "Upload a document image (PNG/JPG). This demo runs a cloud-friendly mode when heavy dependencies are missing. "
    "For full OCR run locally with PaddleOCR/Tesseract installed."
)

uploaded = st.file_uploader("Upload an image (png/jpg) of a document page", type=["png","jpg","jpeg"])

# helper to load demo assets from repo
def load_demo(name):
    base = os.path.join("data", "demo")
    jpath = os.path.join(base, f"{name}.json")
    box_img = os.path.join(base, f"{name}_boxes.png")
    orig = os.path.join(base, f"{name}.png")
    det = {}
    if os.path.exists(jpath):
        with open(jpath, "r", encoding="utf-8") as f:
            det = json.load(f)
    return det, box_img if os.path.exists(box_img) else None, orig if os.path.exists(orig) else None

if not uploaded:
    st.info("You can upload an image, or preview demo examples below.")
    col1, col2 = st.columns(2)
    chosen = None
    with col1:
        if st.button("Show demo: clean_1"):
            chosen = "clean_1"
    with col2:
        if st.button("Show demo: forged_amount_shift"):
            chosen = "forged_amount_shift"
    if chosen:
        det, box_img, orig = load_demo(chosen)
        st.subheader("Demo: " + chosen)
        if orig:
            st.image(orig, width=600)
        if box_img:
            st.image(box_img, width=700, caption="Annotated boxes (red = suspicious)")
        if det:
            st.subheader("Forgery Analysis")
            st.json(det)
        else:
            st.write("Demo data missing. Add JSON/image to data/demo/")
    else:
        st.stop()

# If user uploads file:
if uploaded:
    tmp_path = "tmp_upload.png"
    img = Image.open(uploaded).convert("RGB")
    img.save(tmp_path)
    st.subheader("Preview")
    st.image(tmp_path, width=600)

    if not DEMO_MODE:
        st.info("Running OCR pipeline...")
        try:
            paddle_output = ocr_image(tmp_path)
        except Exception as e:
            st.warning("PaddleOCR error: " + str(e))
            paddle_output = []
        chosen_ocr = paddle_output
        if (not chosen_ocr or all((r.get("text","").strip()=="") for r in chosen_ocr)) and tesseract_ocr:
            st.info("PaddleOCR returned no text → running Tesseract fallback")
            chosen_ocr = tesseract_ocr(tmp_path)
        # run detector
        res = predict(chosen_ocr)
        st.subheader("Forgery Analysis")
        st.json(res)
        # annotated boxes
        try:
            if draw_boxes_fn:
                outimg = "tmp_boxes_highlight.png"
                draw_boxes_fn(tmp_path, chosen_ocr, out_path=outimg)
                st.image(outimg, width=700)
        except Exception as e:
            st.write("Could not draw boxes:", e)
    else:
        st.info("DEMO mode: showing precomputed demo result")
        det, box_img, orig = load_demo("forged_amount_shift")
        if orig:
            st.image(orig, width=600)
        if box_img:
            st.image(box_img, width=700)
        if det:
            st.subheader("Forgery Analysis (demo)")
            st.json(det)
        else:
            st.write("Demo files missing under data/demo/. Add them and redeploy.")
