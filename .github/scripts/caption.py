import json, base64, pathlib, re, os
import google.generativeai as genai
from PIL import Image

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-pro-vision")

IMG_DIR = pathlib.Path("assets/img")
OUT     = pathlib.Path("data/products.json")
products = {}
if OUT.exists():
    products = {p["file"]: p for p in json.loads(OUT.read_text())}

price_re = re.compile(r"_(\d+)$")

for img in IMG_DIR.iterdir():
    if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        continue

    stem = img.stem
    m = price_re.search(stem)
    price = m.group(1) if m else ""
    name  = stem[:m.start()] if m else stem

    if img.name in products and products[img.name].get("desc") and products[img.name].get("price") == price:
        continue

    desc_resp = model.generate_content(
        [img.read_bytes(),
         "請繁體中文活潑口吻，50字以內描述賣點，結尾加 emoji"],
        stream=False
    )
    desc = desc_resp.text.strip()

    products[img.name] = {
        "file": img.name,
        "name": name,
        "price": price,
        "desc": desc
    }

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(list(products.values()), ensure_ascii=False, indent=2))
print("✨ Gemini captions updated!")
`
