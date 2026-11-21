import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from PIL import Image, ImageDraw
import numpy as np

with open(r"E:\Agent\TFTF-blender\scratch\symbol_uv.json") as f:
    data = json.load(f)

img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

for item in data:
    pts = []
    for u, v in item["pts"]:
        x = int(u * 1024)
        y = int((1.0 - v) * 1024)
        pts.append((x, y))
    col = (255, 0, 0, 200) if item["mat"] == 0 else (0, 0, 0, 255)
    draw.polygon(pts, fill=col, outline=(255, 255, 255, 128))

img.save(r"E:\Agent\TFTF-blender\scratch\symbol_uv_layout.png")

# Now load Tx_StarSaber_D.png and see what is under those UVs
tex = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\textures\Tx_StarSaber_D.png").convert("RGBA")
tex = tex.resize((1024, 1024))
tex_np = np.array(tex)

# Overlay the UVs onto the texture
blended = Image.alpha_composite(tex, img)
blended.save(r"E:\Agent\TFTF-blender\scratch\symbol_uv_over_diffuse.png")
print("Saved scratch\\symbol_uv_layout.png and scratch\\symbol_uv_over_diffuse.png")
