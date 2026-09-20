import os
from pathlib import Path
from PIL import Image

ROOT = Path(".")
OUT_DIR = ROOT / "assets_redeco"
OUT_DIR.mkdir(exist_ok=True)

def process_small_icon(src_path, dst_path):
    p = Path(src_path)
    if not p.exists():
        print(f"Skipping missing: {src_path}")
        return
    img = Image.open(p).convert("RGBA")
    # Resize / pad to 128x128
    img = img.resize((128, 128), Image.Resampling.LANCZOS)
    img.save(dst_path, "PNG", optimize=True)
    print(f"Saved {dst_path} ({os.path.getsize(dst_path) / 1024:.1f} KB)")

def process_poster(src_path, dst_path, width=360, height=None):
    p = Path(src_path)
    if not p.exists():
        print(f"Skipping missing: {src_path}")
        return
    img = Image.open(p).convert("RGB")
    orig_w, orig_h = img.size
    if height is None:
        height = int(width * (orig_h / orig_w))
    if height % 2 != 0:
        height += 1
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    resized.save(dst_path, "PNG", optimize=True)
    print(f"Saved {dst_path} ({width}x{height}, {os.path.getsize(dst_path) / 1024:.1f} KB)")

print("=== Processing Quest & Poster Images ===")
# Small quest icons
process_small_icon("飞天虎-small.jpg", OUT_DIR / "portrait_menasor_quest.png")
process_small_icon("盖世擎天柱-small.jpg", OUT_DIR / "portrait_supreme_optimus_quest.png")
process_small_icon(OUT_DIR / "fembots.jpg", OUT_DIR / "portrait_fembots_quest.png")

# Posters
# Act poster fits inside 360x430 so that bottom type/name labels are completely uncovered
process_poster("总海报.jpg", OUT_DIR / "poster_special_act.png", width=360, height=430)
# Chapter 1 poster fits inside 360x360 below the chapter header
process_poster("六道轮回海报.jpg", OUT_DIR / "poster_karmasix.png", width=360, height=360)
process_poster("飞天虎.jpg", OUT_DIR / "poster_menasor.png", width=360)
process_poster("盖世擎天柱.jpg", OUT_DIR / "poster_supreme_optimus.png", width=360)

print("\nDone processing images!")
