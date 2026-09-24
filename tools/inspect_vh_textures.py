# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

tex_dir = Path(r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\textures")
for p in tex_dir.glob("vh_*"):
    im = Image.open(p)
    print(f"Texture: {p.name}, size={im.size}, mode={im.mode}")
