import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from PIL import Image, ImageDraw
import numpy as np

with open(r"E:\Agent\TFTF-blender\scratch\body_uvs.json") as f:
    polys = json.load(f)

img = Image.new("L", (1024, 1024), 0)
draw = ImageDraw.Draw(img)

for poly in polys:
    pts = []
    for u, v in poly:
        x = int(u * 1024) % 1024
        y = int((1.0 - v) * 1024) % 1024
        pts.append((x, y))
    draw.polygon(pts, fill=255)

coverage = np.array(img) > 0
print(f"Body UV coverage: {coverage.mean()*100:.1f}%")

# Save UV map overlay on Diffuse
diff = Image.open(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\StarSaber\Textures\cha_starsaber_main_Diffuse.png").resize((1024, 1024))
diff_arr = np.array(diff)
overlay = diff_arr.copy()
overlay[coverage, 0] = np.clip(overlay[coverage, 0].astype(int) + 60, 0, 255)
Image.fromarray(overlay).save(r"E:\Agent\TFTF-blender\scratch\uv_coverage_diffuse.png")

# Find contiguous empty boxes
step = 64
empty_blocks = []
for y in range(0, 1024 - step, step):
    for x in range(0, 1024 - step, step):
        patch = coverage[y:y+step, x:x+step]
        if not patch.any():
            empty_blocks.append((x, y))

print(f"Empty 64x64 blocks count: {len(empty_blocks)}")
for b in empty_blocks:
    if b[0] + 128 <= 1024 and b[1] + 128 <= 1024:
        patch128 = coverage[b[1]:b[1]+128, b[0]:b[0]+128]
        if not patch128.any():
            print(f"  Empty 128x128: X=[{b[0]}..{b[0]+128}], Y=[{b[1]}..{b[1]+128}] -> UV: U=[{b[0]/1024:.3f}..{(b[0]+128)/1024:.3f}], V=[{1-(b[1]+128)/1024:.3f}..{1-b[1]/1024:.3f}]")
