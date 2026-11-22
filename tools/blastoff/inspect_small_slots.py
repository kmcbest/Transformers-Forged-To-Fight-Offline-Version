import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")

for fname, name, (x0, y0, x1, y1) in [
    ("rb_blastoff_chest_cust_matinst.jpg", "Chest Grille LeftHalf", (15, 390, 190, 485)),
    ("rb_blastoff_legs_cust_matinst.jpg", "Shin MidRight Strip1", (700, 175, 760, 250)),
    ("rb_blastoff_legs_cust_matinst.jpg", "Shin MidRight Strip2", (935, 255, 1000, 345)),
    ("rb_blastoff_legs_cust_matinst.jpg", "Shin Center Slit", (425, 425, 470, 525)),
]:
    arr = np.array(Image.open(SRC / fname).convert("RGB"))[y0:y1, x0:x1]
    r, g, b = arr[:,:,0].astype(int), arr[:,:,1].astype(int), arr[:,:,2].astype(int)
    # Find pixels with highest (b - g)
    bg = b - g
    top = bg >= max(4, np.percentile(bg, 85))
    print(f"{name}: max(b-g)={bg.max()}, p95(b-g)={np.percentile(bg,95):.1f}, sample top RGBs:")
    pts = arr[bg >= np.percentile(bg, 92)]
    print(f"  mean={pts.mean(axis=0).round(1)}, max={pts.max(axis=0)}, count_bg>5={(bg>5).sum()}")
