import os
from PIL import Image, ImageDraw, ImageFont
import json

os.makedirs("data/demo", exist_ok=True)

# Try to use a default font
try:
    font = ImageFont.truetype("arial.ttf", 40)
except:
    font = ImageFont.load_default()

def make_demo(name, account, amount, forged_extra=None):
    """
    name: person name
    account: account number
    amount: main amount
    forged_extra: another amount to simulate forgery (optional)
    """

    # Create blank white image 1000x1400
    img = Image.new("RGB", (1000, 1400), "white")
    draw = ImageDraw.Draw(img)

    y = 200
    draw.text((150, y), f"Name: {name}", fill="black", font=font); y += 150
    draw.text((150, y), f"Account: {account}", fill="black", font=font); y += 150
    draw.text((150, y), f"Amount: Rs {amount:,}", fill="black", font=font); y += 150
    draw.text((150, y), "Date: 2025-12-01", fill="black", font=font); y += 150
    draw.text((150, y), "Signature: ___________", fill="black", font=font)

    # Save clean image
    clean_path = f"data/demo/{name.lower()}_clean.png"
    img.save(clean_path)

    # Save OCR JSON (simulated Tesseract output)
    json_path = f"data/demo/{name.lower()}_clean_ocr.json"
    json.dump({
        "text_lines": [
            f"Name: {name}",
            f"Account: {account}",
            f"Amount: Rs {amount:,}",
            "Date: 2025-12-01",
            "Signature:"
        ],
        "amounts": [amount],
        "forged": False
    }, open(json_path, "w"), indent=2)

    print("Saved:", clean_path, json_path)

    # If forged requested
    if forged_extra:
        forged_img = img.copy()
        draw2 = ImageDraw.Draw(forged_img)
        draw2.text((150, y + 150), f"Amount: Rs {forged_extra:,}", fill="red", font=font)

        forged_path = f"data/demo/{name.lower()}_forged.png"
        forged_img.save(forged_path)

        forged_json = f"data/demo/{name.lower()}_forged_ocr.json"
        json.dump({
            "text_lines": [
                f"Name: {name}",
                f"Account: {account}",
                f"Amount: Rs {amount:,}",
                f"Amount: Rs {forged_extra:,}",
                "Date: 2025-12-01",
                "Signature:"
            ],
            "amounts": [amount, forged_extra],
            "forged": True
        }, open(forged_json, "w"), indent=2)

        print("Saved:", forged_path, forged_json)


# ----------------------
# Generate two demo sets
# ----------------------

make_demo(
    name="DemoUser",
    account=1234567890,
    amount=20000,
    forged_extra=200000
)

print("\nDemo files generated successfully!")
