import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
h_diff = Image.open(SRC / "rb_blastoff_head_cust_matinst.jpg")
arr = np.array(h_diff)

crop = arr[200:260, 190:320]
print(f"Crop shape: {crop.shape}")

# Let's save a crop to inspect
Image.fromarray(crop).save(r"E:\Agent\TFTF-blender\renders\blastoff\eye_crop.png")
print("Saved eye_crop.png")

# Let's see colors in this region
for y in range(200, 240, 4):
    row_pixels = []
    for x in range(195, 315, 8):
        row_pixels.append(f"({arr[y,x,0]},{arr[y,x,1]},{arr[y,x,2]})")
    print(f"Y={y}: " + " ".join(row_pixels))
