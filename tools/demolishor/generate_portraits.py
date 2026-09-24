# -*- coding: utf-8 -*-
"""
generate_portraits.py
Generates in-game portraits for Demolishor (large, quest, small)
"""

import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

diffuse_path = Path("tools/demolishor/textures_processed/cha_demolishor_main_a.png")
out_dir = Path("assets_redeco")

img = Image.open(diffuse_path).convert("RGBA")

# In Demolishor's diffuse map, find chest/head region or center crop
w, h = img.size
# Center crop with 1:1 aspect ratio focusing on upper body
crop_box = (int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85))
cropped = img.crop(crop_box)

# 1. Large Portrait (256x256 PNG)
large = cropped.resize((256, 256), Image.Resampling.LANCZOS)
large_path = out_dir / "portrait_demolishor_large.png"
large.save(large_path, format="PNG")
print(f"[✓] Saved {large_path}")

# 2. Quest Portrait (256x256 PNG)
quest_path = out_dir / "portrait_demolishor_quest.png"
large.save(quest_path, format="PNG")
print(f"[✓] Saved {quest_path}")

# 3. Small Portrait (538x538 JPEG)
small = cropped.resize((538, 538), Image.Resampling.LANCZOS).convert("RGB")
small_path = out_dir / "portrait_demolishor_small.jpg"
small.save(small_path, format="JPEG", quality=90)
print(f"[✓] Saved {small_path}")
