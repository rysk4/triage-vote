#!/usr/bin/env python3
import os
import shutil
from PIL import Image, ImageDraw, ImageFont

# (proposal_number, likes, dislikes, score) — seřazeno dle score DESC
RESULTS = [
    (16, 4, 0, 4),
    (11, 2, 0, 2),
    (4, 2, 0, 2),
    (33, 2, 0, 2),
    (19, 2, 1, 1),
    (10, 1, 0, 1),
    (13, 1, 0, 1),
    (25, 1, 0, 1),
    (5, 1, 0, 1),
    (1, 1, 0, 1),
    (34, 1, 0, 1),
    (14, 1, 0, 1),
    (36, 1, 1, 0),
    (22, 1, 2, -1),
    (27, 0, 1, -1),
    (9, 0, 1, -1),
    (26, 0, 1, -1),
    (28, 0, 1, -1),
    (35, 0, 1, -1),
    (2, 0, 1, -1),
    (20, 0, 1, -1),
    (29, 0, 3, -3),
]

SRC = "/Users/clovek/Desktop/_claude_code/triage_vote/zdroje-01"
DST = "/Users/clovek/Desktop/_claude_code/triage_vote/vysledky"

os.makedirs(DST, exist_ok=True)

# pokus o systémový font
font_candidates = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]
font_path = next((p for p in font_candidates if os.path.exists(p)), None)

for rank, (num, likes, dislikes, score) in enumerate(RESULTS, start=1):
    src_name = f"merch_munchen-{num+1:02d}.jpg"
    src_path = os.path.join(SRC, src_name)
    if not os.path.exists(src_path):
        print(f"MISSING: {src_path}")
        continue

    img = Image.open(src_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # text: "#16  +4  (4/0)" — návrh, skóre, poměr
    sign = "+" if score > 0 else ""
    label = f"#{num}  {sign}{score}  ({likes}/{dislikes})"

    # velikost fontu ~ 4% šířky obrázku
    fs = max(20, int(W * 0.045))
    try:
        font = ImageFont.truetype(font_path, fs) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = max(8, fs // 3)
    bw, bh = tw + pad * 2, th + pad * 2

    margin = max(12, fs // 2)
    x0, y0 = margin, margin
    x1, y1 = x0 + bw, y0 + bh

    # červený box
    draw.rectangle([x0, y0, x1, y1], fill=(220, 30, 30))
    # bílý text
    draw.text((x0 + pad - bbox[0], y0 + pad - bbox[1]), label, fill=(255, 255, 255), font=font)

    out_name = f"{rank:02d}_navrh-{num:02d}_score{sign}{score}.jpg"
    out_path = os.path.join(DST, out_name)
    img.save(out_path, quality=92)
    print(f"{rank:02d}. #{num:2d}  score={sign}{score:+d}  →  {out_name}")

print(f"\nHotovo. {len(RESULTS)} obrázků v {DST}")
