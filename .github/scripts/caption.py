import json, pathlib, re, os
from PIL import Image
from google import genai                          # ← 新寫法

# --------- 初始化 ---------
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
model  = client.models.get("gemini-pro-vision")   # 也可換成 gemini-2.0-flash

IMG_DIR = pathlib.Path("assets/img")
OUT     = pathlib.Path("data/products.json")

products = {}
if OUT.exists():
    products = {p["file"]: p for p in json.loads(OUT.read_text())}

price_re = re.compile(r"_(\d+)$")   # 抓 _數字 當價格

# --------- 逐張圖片處理 ---------
for img in IMG_DIR.iterdir():
    if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        continue

    stem = img.stem
    m    = price_re.search(stem)
    price = m.group(1) if m else ""
    name  = stem[:m.start()] if m else stem

    # 已有描述且價格相同就跳過
    if img.name in products and products[img.name].get("desc") and products[img.name].get("price") == price:
        continue

    # ☆ 關鍵：傳 PIL.Image.Image 物件給 Gemini
    pil_img = Image.open(img)

    resp = model.generate_content(
        [pil_img, "請繁體中文活潑口吻，50字以內描述賣點，結尾加 emoji"],
        stream=False
    )
    desc = resp.text.strip()

    products[img.name] = {
        "file": img.name,
        "name": name,
        "price": price,
        "desc": desc
    }

# --------- 輸出 ---------
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(list(products.values()), ensure_ascii=False, indent=2))
print("✨ Gemini captions updated!")
