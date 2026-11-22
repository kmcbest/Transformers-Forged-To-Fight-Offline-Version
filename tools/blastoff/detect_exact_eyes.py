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

# Detect eye pixels: in crop [200:222, 190:320]
# Eye pixels are distinctly purple: B > R and B > 1.2 * G and B > 90
eye_mask = np.zeros((512, 512), dtype=np.uint8)

# Left eye box: X in [190, 230], Y in [201, 220]
# Right eye box: X in [280, 320], Y in [201, 220]
for y in range(200, 222):
    for x in list(range(190, 230)) + list(range(280, 320)):
        r, g, b = int(arr[y, x, 0]), int(arr[y, x, 1]), int(arr[y, x, 2])
        # Check purple hue: B > 90 and B > G + 30 and R > G + 15
        if b > 90 and b > g + 30 and r > g + 15:
            eye_mask[y, x] = 255

print(f"Total eye pixels detected: {np.sum(eye_mask > 0)}")
y_indices, x_indices = np.where(eye_mask > 0)
print(f"Eye mask X bounds: [{x_indices.min()}, {x_indices.max()}], Y bounds: [{y_indices.min()}, {y_indices.max()}]")

# Let's save a visualization overlay
overlay = arr.copy()
overlay[eye_mask > 0] = [255, 0, 255]
Image.fromarray(overlay[190:240, 180:330]).save(r"E:\Agent\TFTF-blender\renders\blastoff\eye_mask_preview.png")
print("Saved eye_mask_preview.png")
