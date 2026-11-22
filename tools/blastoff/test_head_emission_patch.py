import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
head_diff = Image.open(SRC / "rb_blastoff_head_cust_matinst.jpg").convert("RGB")
head_e = Image.open(SRC / "head_e.jpg").convert("RGB")

diff = np.array(head_diff, dtype=np.uint8)
em_rgb = np.array(head_e, dtype=np.uint8)
em_mask = np.clip((em_rgb.max(axis=2).astype(np.float32) - 15) / 165.0, 0.0, 1.0)
em_mask = (em_mask * 255.0).astype(np.uint8)

# 1. Clear crown vents
em_mask[120:190, 0:190] = 0
em_rgb[120:190, 0:190] = 0

# 2. Paint eyes
eye_lit_count = 0
for box_x, box_y in [((191, 226), (201, 221)), ((288, 323), (201, 221))]:
    x0, x1 = box_x
    y0, y1 = box_y
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = [int(v) for v in diff[y, x]]
            is_frame = (r > 120 and g > 115 and abs(r - g) < 22 and abs(r - b) < 25)
            is_visor = not is_frame and (b > g + 8 or (r < 110 and g < 110 and b < 125))
            if is_visor:
                em_mask[y, x] = 255
                em_rgb[y, x] = [245, 50, 255]
                diff[y, x] = [245, 60, 255]
                eye_lit_count += 1

print(f"Total eye pixels lit: {eye_lit_count}")
print(f"Crown vents lit pixels: {np.count_nonzero(em_mask[120:190, 0:190] > 0)}")

# Save preview of head tile diff and emission
preview_dir = Path("renders/blastoff")
preview_dir.mkdir(parents=True, exist_ok=True)
Image.fromarray(diff).save(preview_dir / "head_diff_test.png")
Image.fromarray(em_mask).save(preview_dir / "head_em_test.png")
print(f"Saved previews to {preview_dir}")
