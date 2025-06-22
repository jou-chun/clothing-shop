import json, base64, pathlib, re, os, time
from PIL import Image
from openai import OpenAI

# ─── 0. 基本設定 ─────────────────────────
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL  = "gpt-4o"                           # 或 gpt-4o-2024-08-06 等快照

IMG_DIR = pathlib.Path("assets/img")
OUT     = pathlib.Path("data/products.json")

price_re = re.compile(r"_(\d+)$")          # 擷取 _價格
order_re = re.compile(r"^(\d+)[-_]")       # 讀檔名前綴排序

# 讀舊 JSON → dict 方便查詢
old = {}
if OUT.exists():
    for p in json.loads(OUT.read_text()):
        old[p["file"]] = p

# ─── 1. 取得現有圖片，依「檔案修改時間」新→舊排序 ──
imgs = sorted(
    (f for f in IMG_DIR.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png"}),
    key=lambda f: f.stat().st_mtime,
    reverse=True
)

new_products = []

for img in imgs:
    stem  = img.stem
    m     = price_re.search(stem)
    price = m.group(1) if m else ""
    name_part = stem[:m.start()] if m else stem
    o = order_re.match(name_part)
    order = int(o.group(1)) if o else None
    name  = order_re.sub("", name_part, 1) if o else name_part

    # 已經有描述 & 價格沒變 → 直接沿用舊資料
    if img.name in old and old[img.name].get("price") == price:
        new_products.append(old[img.name])
        continue

    # 需要生成新描述
    b64 = base64.b64encode(img.read_bytes()).decode()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system",
             "content":"你是時尚電商小編，50 字以內活潑口吻。"},
            {"role":"user",
             "content":[
                {"type":"image_url",
                 "image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
                {"type":"text",
                 "text":"請繁體中文描述這件衣服的賣點，結尾加 emoji"}
             ]}
        ]
    )
    desc = resp.choices[0].message.content.strip()

    item = {
        "file": img.name,
        "name": name,
        "price": price,
        "desc":  desc
    }
    if order is not None:
        item["order"] = order
    new_products.append(item)

# ─── 2. 輸出（覆蓋舊 JSON；刪掉的圖片自動消失） ──
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(new_products, ensure_ascii=False, indent=2))
print(f"✨ Updated {len(new_products)} products (newest first)")
