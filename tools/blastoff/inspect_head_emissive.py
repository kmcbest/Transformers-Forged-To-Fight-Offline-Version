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
h_e = Image.open(SRC / "head_e.jpg")

arr_diff = np.array(h_diff)
arr_e = np.array(h_e)

print(f"rb_blastoff_head_cust_matinst: {arr_diff.shape}")
print(f"head_e.jpg: {arr_e.shape}")

# Where are pixels in head_e lit?
lit_y, lit_x = np.where(arr_e.max(axis=2) > 30)
print(f"Lit pixels in head_e: {len(lit_y)}")
if len(lit_y) > 0:
    for idx in range(min(5, len(lit_y))):
        y, x = lit_y[idx], lit_x[idx]
        print(f"   lit pixel at ({x}, {y}): RGB={arr_e[y, x]}")
    print(f"Lit bounding box: X=[{lit_x.min()}, {lit_x.max()}], Y=[{lit_y.min()}, {lit_y.max()}]")

# Now let's see what is in arr_diff at those lit pixels!
if len(lit_y) > 0:
    print(f"Diff color at lit pixels: mean={arr_diff[lit_y, lit_x].mean(axis=0)}")

# Are there purple/pink/magenta pixels in arr_diff?
# In FOC, visor/eyes often have colored pixels in Diffuse!
lum = arr_diff.mean(axis=2)
# Purple has R > 100, B > 100, G < 80
purple_y, purple_x = np.where((arr_diff[:, :, 0] > 100) & (arr_diff[:, :, 2] > 100) & (arr_diff[:, :, 1] < 80))
print(f"Purple pixels in rb_blastoff_head_cust_matinst: {len(purple_y)}")
if len(purple_y) > 0:
    print(f"Purple bounding box: X=[{purple_x.min()}, {purple_x.max()}], Y=[{purple_y.min()}, {purple_y.max()}]")
    for idx in range(min(5, len(purple_y))):
        y, x = purple_y[idx], purple_x[idx]
        print(f"   purple pixel at ({x}, {y}): RGB={arr_diff[y, x]}")

# What about all files in SRC that end with _e.jpg?
for f in SRC.glob("*_e*.jpg"):
    print(f"Emissive file: {f.name}")
