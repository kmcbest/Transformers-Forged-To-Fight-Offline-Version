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

# Let's inspect the entire row Y=206 across X=180..350
print("Y=206:")
for x in range(185, 335, 2):
    px = arr[206, x]
    # Check if purple: B > R and B > G
    is_p = (px[2] > px[0]) and (px[2] > px[1] + 20)
    tag = " *PURPLE*" if is_p else ""
    if is_p or (190 <= x <= 228) or (280 <= x <= 325):
        print(f"  X={x}: {px.tolist()}{tag}")

# Let's find all purple pixels in Y in [195, 225]
y_indices, x_indices = np.where((arr[195:225, :, 2] > arr[195:225, :, 0] + 15) & (arr[195:225, :, 2] > arr[195:225, :, 1] + 25))
y_indices += 195
print(f"\nAll detected eye slit pixels in Y=[195, 225]: count={len(x_indices)}")
print(f"X range: {x_indices.min()} to {x_indices.max()}")
print(f"Y range: {y_indices.min()} to {y_indices.max()}")

# Cluster them into left eye and right eye
left_eye = [(x, y) for x, y in zip(x_indices, y_indices) if x < 250]
right_eye = [(x, y) for x, y in zip(x_indices, y_indices) if x >= 250]
if left_eye:
    lx = [p[0] for p in left_eye]
    ly = [p[1] for p in left_eye]
    print(f"Left eye: X=[{min(lx)}, {max(lx)}], Y=[{min(ly)}, {max(ly)}], count={len(left_eye)}")
if right_eye:
    rx = [p[0] for p in right_eye]
    ry = [p[1] for p in right_eye]
    print(f"Right eye: X=[{min(rx)}, {max(rx)}], Y=[{min(ry)}, {max(ry)}], count={len(right_eye)}")
