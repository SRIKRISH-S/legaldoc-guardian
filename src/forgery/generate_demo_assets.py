from PIL import Image, ImageDraw, ImageFont
import os, json

os.makedirs("data/demo", exist_ok=True)

W, H = 1200, 1600
left_col = 140
text_x = 360

def get_font(sz=36):
    try:
        return ImageFont.truetype("arial.ttf", sz)
    except:
        return ImageFont.load_default()

font_h = get_font(36)
font_val = get_font(44)

def text_width(draw, text, font):
    """Return width of text using textbbox (Pillow-safe)."""
    if not text:
        return 200
    bbox = draw.textbbox((0,0), text, font=font)
    return bbox[2] - bbox[0]

def make_clean(path_img, path_box, path_json):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((left_col, 80), "Bank Payment Slip", font=get_font(56), fill="black")

    fields = [
        ("Name:", "SRIKRISHNA", (text_x, 240)),
        ("Account:", "1234567890", (text_x, 360)),
        ("Amount:", "Rs 20,000", (text_x, 510)),
        ("Date:", "2025-12-01", (text_x, 660)),
        ("Signature:", "", (text_x, 820)),
    ]

    boxes = []
    for label, val, (x,y) in fields:
        d.text((left_col, y), label, font=font_h, fill="black")
        d.text((x, y), val, font=font_val, fill="black")
        w = text_width(d, val, font_val)
        h = 60
        bx = [[x-6, y-6], [x+w+6, y-6], [x+w+6, y+h+6], [x-6, y+h+6]]
        boxes.append({"box": bx, "text": val, "conf": 95.0})

    img.save(path_img)

    annotated = img.copy()
    draw2 = ImageDraw.Draw(annotated)
    for b in boxes:
        pts = [tuple(p) for p in b["box"]]
        draw2.line(pts + [pts[0]], width=4, fill=(0,200,0))
    annotated.save(path_box)

    output = {
        "label": "CLEAN",
        "score": 0.12,
        "fields": {
            "name": "SRIKRISHNA",
            "account": "1234567890",
            "amounts": [20000],
            "raw_text": "Name: SRIKRISHNA\nAccount: 1234567890\nAmount: Rs 20,000\nDate: 2025-12-01\nSignature:"
        },
        "evidence": []
    }
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

def make_forged(path_img, path_box, path_json):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((left_col, 80), "Bank Payment Slip", font=get_font(56), fill="black")

    fields = [
        ("Name:", "SRIKRISHNA", (text_x, 240)),
        ("Account:", "1234567890", (text_x, 360)),
        ("Amount:", "Rs 20,000", (text_x, 510)),
        ("Date:", "2025-12-01", (text_x, 660)),
        ("Signature:", "", (text_x, 820)),
    ]

    boxes = []
    for label, val, (x,y) in fields:
        d.text((left_col, y), label, font=font_h, fill="black")
        d.text((x, y), val, font=font_val, fill="black")
        w = text_width(d, val, font_val)
        h = 60
        bx = [[x-6, y-6], [x+w+6, y-6], [x+w+6, y+h+6], [x-6, y+h+6]]
        boxes.append({"box": bx, "text": val, "conf": 95.0})

    # forged entry
    forged_text = "Rs 2,00,000"
    fx, fy = 720, 1020
    d.text((fx, fy), "Amount:", font=font_h, fill="black")
    d.text((fx+220, fy), forged_text, font=font_val, fill="black")

    w_f = text_width(d, forged_text, font_val)
    h_f = 60
    bx_f = [[fx+220-6, fy-6], [fx+220+w_f+6, fy-6], [fx+220+w_f+6, fy+h_f+6], [fx+220-6, fy+h_f+6]]
    boxes.append({"box": bx_f, "text": forged_text, "conf": 92.0})

    img.save(path_img)

    annotated = img.copy()
    draw2 = ImageDraw.Draw(annotated)
    for i,b in enumerate(boxes):
        pts = [tuple(p) for p in b["box"]]
        color = (255,0,0) if i == len(boxes)-1 else (0,200,0)
        draw2.line(pts + [pts[0]], width=4, fill=color)
    annotated.save(path_box)

    output = {
        "label": "FORGED",
        "score": 0.9,
        "fields": {
            "name": "SRIKRISHNA",
            "account": "1234567890",
            "amounts": [20000, 200000],
            "raw_text":
                "Name: SRIKRISHNA\n"
                "Account: 1234567890\n"
                "Amount: Rs 20,000\n"
                "Date: 2025-12-01\n"
                "Signature:\n"
                "Amount: Rs 2,00,000"
        },
        "evidence": ["multiple_amounts_detected:[20000,200000]"]
    }
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)


clean_img = "data/demo/clean_1.png"
clean_box = "data/demo/clean_1_boxes.png"
clean_json = "data/demo/clean_1.json"

forged_img = "data/demo/forged_amount_shift.png"
forged_box = "data/demo/forged_amount_shift_boxes.png"
forged_json = "data/demo/forged_amount_shift.json"

make_clean(clean_img, clean_box, clean_json)
make_forged(forged_img, forged_box, forged_json)

print("Demo assets generated successfully!")
