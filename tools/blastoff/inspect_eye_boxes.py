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
arr = np.array(head_diff)

# Let's inspect the left eye box [190:222, 201:220]
# and right eye box [288:320, 201:220]
print("--- Left eye box pixel analysis ---")
for y in range(202, 220):
    row_str = ""
    for x in range(192, 222):
        px = arr[y, x]
        # Is purple or dark inner slit
        is_purple = (px[2] > px[0] and px[2] > px[1] + 15) or (px[0] > 70 and px[2] > 110)
        row_str += "P " if is_purple else ". "
    print(f"Y={y}: {row_str}")

print("\n--- Right eye box pixel analysis ---")
for y in range(202, 220):
    row_str = ""
    for x in range(290, 320):
        px = arr[y, x]
        is_purple = (px[2] > px[0] and px[2] > px[1] + 15) or (px[0] > 70 and px[2] > 110)
        row_str += "P " if is_purple else ". "
    print(f"Y={y}: {row_str}")
