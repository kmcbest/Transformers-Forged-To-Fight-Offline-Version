# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

diffuse_path = Path("tools/demolishor/textures_processed/cha_demolishor_main_a.png")
if diffuse_path.exists():
    img = Image.open(diffuse_path)
    print(f"Diffuse loaded: {img.size}")
    
    # We can create square portrait from texture or face region
    # Also let's check breakdown's portrait size
    for p in Path("assets_redeco").glob("portrait_breakdown*"):
        p_img = Image.open(p)
        print(f"  Sample portrait {p.name}: {p_img.size}, {p_img.mode}")
