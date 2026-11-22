import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
head_diff = Image.open(SRC / "rb_blastoff_head_cust_matinst.jpg")
head_e = Image.open(SRC / "head_e.jpg")

print(f"head_diff size: {head_diff.size}, mode: {head_diff.mode}")
print(f"head_e size: {head_e.size}, mode: {head_e.mode}")

arr_e = np.array(head_e)
print(f"head_e non-zero count: {np.count_nonzero(arr_e > 20)}")
# Find bounding box of bright pixels in head_e
bright_y, bright_x = np.where(arr_e.mean(axis=2) > 30)
if len(bright_y) > 0:
    print(f"head_e bright bbox: X=[{bright_x.min()}, {bright_x.max()}], Y=[{bright_y.min()}, {bright_y.max()}]")

# Now check head_diff where purple or bright
arr_diff = np.array(head_diff)
# Purple detection: R > 100, B > 100, G < 80
purple_mask = (arr_diff[:, :, 0] > 80) & (arr_diff[:, :, 2] > 100) & (arr_diff[:, :, 1] < 100)
py, px = np.where(purple_mask)
if len(py) > 0:
    print(f"head_diff purple bbox: X=[{px.min()}, {px.max()}], Y=[{py.min()}, {py.max()}]")
    print(f"Number of purple pixels: {len(py)}")

# Let's inspect areas around Y=[180, 240] and X=[180, 330]
print("\nInspecting Diffuse values in the eye band Y=200..220:")
for y in range(200, 222, 2):
    row_pixels = [(x, arr_diff[y, x].tolist()) for x in range(190, 230, 4)]
    # print if not mostly zero
    print(f"Y={y}: {row_pixels[:5]}")
