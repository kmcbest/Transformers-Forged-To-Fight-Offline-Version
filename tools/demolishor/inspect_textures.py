# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

tex_dir = Path(r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\textures")

for img_file in tex_dir.glob("rb_*.jpeg"):
    img = Image.open(img_file)
    print(f"Texture: {img_file.name}, Size: {img.size}, Mode: {img.mode}, Format: {img.format}")
