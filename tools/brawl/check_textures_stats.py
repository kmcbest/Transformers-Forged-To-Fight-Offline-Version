import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

TEX_DIR = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")

for fname in [
    "rb_brawl_head_mat_inst_e.jpg",
    "rb_brawl_chest_mat_inst_e.jpg",
    "rb_brawl_legs_mat_inst_e.jpg",
    "vh_brawl_cust_matinst_e.jpg",
    "DecepticonLogo.png",
]:
    p = TEX_DIR / fname
    im = Image.open(p)
    arr = np.array(im)
    print(f"{fname:32s}: mode={im.mode:4s} size={im.size} min={arr.min()} max={arr.max()}")
    if fname.endswith("_e.jpg"):
        lum = arr.max(axis=2) if arr.ndim == 3 else arr
        for thr in (30, 80, 120):
            pct = (lum > thr).mean() * 100
            if (lum > thr).any() and arr.ndim == 3:
                mrgb = arr[lum > thr].mean(axis=0)
                print(f"    >{thr:3d}: {pct:5.2f}% meanRGB={np.round(mrgb, 1)}")
            else:
                print(f"    >{thr:3d}: {pct:5.2f}%")
