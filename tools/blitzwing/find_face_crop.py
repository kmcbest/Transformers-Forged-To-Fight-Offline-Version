import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
from pathlib import Path

TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Textures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

body_img = Image.open(TEX_DIR / "Body.jpg")
w, h = body_img.size

# Crop head region (U: 0.0 ~ 0.4, V: 0.0 ~ 0.4 or similar)
# In image coords: x = u * w, y = (1 - v) * h
crop_box = (0, 0, int(0.4 * w), int(0.5 * h))
crop_img = body_img.crop(crop_box)
crop_img.save(OUT_DIR / "debug_head_crop.png")
print(f"[✓] Saved debug_head_crop.png ({crop_img.size})")
