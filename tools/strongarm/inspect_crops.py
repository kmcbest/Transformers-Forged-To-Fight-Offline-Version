import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

tex_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.png")
im = Image.open(tex_path)
w, h = im.size

# In Blender UV: (0, 0) is bottom-left, (1, 1) is top-right.
# In PIL Image: (0, 0) is top-left, (w, h) is bottom-right.
# So PIL_y = h - (V * h).

def uv_to_pil(u, v):
    return int(u * w), int((1.0 - v) * h)

# Crop 1: +Z faces
px1, py1 = uv_to_pil(0.616, 0.588)
crop1 = im.crop((max(0, px1-40), max(0, py1-40), min(w, px1+40), min(h, py1+40)))
crop1.save(r"E:\Agent\TFTF-blender\tools\strongarm\crop_pos_z.png")

# Crop 2: -Z faces
px2, py2 = uv_to_pil(0.452, 0.822)
crop2 = im.crop((max(0, px2-40), max(0, py2-40), min(w, px2+40), min(h, py2+40)))
crop2.save(r"E:\Agent\TFTF-blender\tools\strongarm\crop_neg_z.png")

print(f"Crop 1 (+Z): center at ({px1}, {py1})")
print(f"Crop 2 (-Z): center at ({px2}, {py2})")
