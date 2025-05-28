import json, base64, pathlib, re, os
from PIL import Image
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o"        # 之後官方改名只要換這裡

IMG_DIR = pathlib.Path("assets/img")
OUT     = pathlib.Path("data/products.json")
products = {}
if OUT.exists():
    products = {p["file"]: p for p in json.loads(OUT.read_text())}

price_re = re.compile(r"_(\d+)$")      # 擷取 _價格

for img in IMG_DIR.iterdir():
    if img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        continue

    stem  = img.stem
    m     = price_re.search(stem)
    price = m.group(1) if m else ""
    name  = stem[:m.start()] if m else stem

    # 若已生成且價格未變，略過
    if img.name in products and products[img.name].get("desc") and products[img.name].get("price") == price:
        continue

    # 轉 base64 → GPT-4o Vision
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

    products[img.name] = {
        "file": img.name,
        "name": name,
        "price": price,
        "desc": desc
    }

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(list(products.values()), ensure_ascii=False, indent=2))
print("✨ OpenAI captions updated!")

