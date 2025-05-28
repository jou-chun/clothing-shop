{\rtf1\ansi\ansicpg950\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import json, base64, pathlib, re, os\
import google.generativeai as genai\
from PIL import Image\
\
### 0. \uc0\u21021 \u22987 \u21270  ###\
genai.configure(api_key=os.environ["GEMINI_API_KEY"])\
model = genai.GenerativeModel("gemini-pro-vision")   # \uc0\u22810 \u27169 \u24907 \u27169 \u22411 \
\
IMG_DIR = pathlib.Path("assets/img")\
OUT     = pathlib.Path("data/products.json")\
\
### 1. \uc0\u35712 \u33290 \u21830 \u21697 \u36039 \u26009  ###\
products = \{\}\
if OUT.exists():\
    products = \{p["file"]: p for p in json.loads(OUT.read_text())\}\
\
### 2. \uc0\u27491 \u21063 \u25235 \u27284 \u21517 \u20013 \u30340 \u20729 \u26684 \u65288 _1234\u65289 ###\
price_re = re.compile(r"_(\\d+)$")   # \uc0\u12300 \u24213 \u32218 +\u25976 \u23383 \u12301 \u35222 \u28858 \u20729 \u26684 \
\
### 3. \uc0\u36880 \u24373 \u22294 \u29255 \u34389 \u29702  ###\
for img in IMG_DIR.iterdir():\
    if img.suffix.lower() not in \{".jpg", ".jpeg", ".png"\}:\
        continue\
\
    stem = img.stem\
    price_m = price_re.search(stem)\
    price = price_m.group(1) if price_m else ""\
    name  = stem[:price_m.start()] if price_m else stem\
\
    # \uc0\u33509 \u24050 \u32147 \u26377 \u25551 \u36848 \u19988 \u20729 \u26684 \u30456 \u21516 \u65292 \u36339 \u36942 \
    if img.name in products and products[img.name].get("desc") and products[img.name].get("price") == price:\
        continue\
\
    # \uc0\u35712  bytes \u8594  Gemini\
    img_bytes = img.read_bytes()\
    resp = model.generate_content(\
        [img_bytes, "\uc0\u35531 \u32321 \u39636 \u20013 \u25991 \u27963 \u28497 \u21475 \u21563 \u65292 50\u23383 \u20839 \u25551 \u36848 \u36067 \u40670 \u65292 \u32080 \u23614 \u21152  emoji"],\
        stream=False,     # \uc0\u19981 \u29992 \u20018 \u27969 \
        safety_settings=\{"HARASSMENT": "block_none"\}  # \uc0\u21487 \u30465 \u30053 \u65292 \u31034 \u31684 \u23531 \u27861 \
    )  # \uc0\u21443 \u32771 \u23448 \u26041 \u31034 \u20363  :contentReference[oaicite:1]\{index=1\}\
\
    desc = resp.text.strip()\
\
    products[img.name] = \{\
        "file": img.name,\
        "name": name,\
        "price": price,\
        "desc": desc\
    \}\
\
### 4. \uc0\u36664 \u20986  ###\
OUT.parent.mkdir(exist_ok=True)\
OUT.write_text(json.dumps(list(products.values()), ensure_ascii=False, indent=2))\
print("\uc0\u10024  Gemini captions updated!")\
}