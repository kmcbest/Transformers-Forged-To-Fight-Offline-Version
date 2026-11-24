import sys
from pathlib import Path
from PIL import Image
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"

v1_t = np.array(Image.open(SRC_DIR / "H_shandian_G1_V1_T.png").convert("RGB"))
v1_rgba = np.array(Image.open(SRC_DIR / "H_shandian_G1_V1_T.png"))

# Where is alpha < 255 in V1?
if v1_rgba.shape[2] == 4:
    is_glass = v1_rgba[:, :, 3] < 250
    print(f"V1 glass/canopy pixels (alpha < 250): {is_glass.sum():,} ({is_glass.mean()*100:.3f}%)")
    if is_glass.sum() > 0:
        print(f"  Glass color sample: RGB = {v1_t[is_glass][0]}")

v2_rgba = np.array(Image.open(SRC_DIR / "H_shandian_G1_V2_T.png"))
if v2_rgba.shape[2] == 4:
    is_glass2 = v2_rgba[:, :, 3] < 250
    print(f"V2 glass/canopy pixels (alpha < 250): {is_glass2.sum():,} ({is_glass2.mean()*100:.3f}%)")
    if is_glass2.sum() > 0:
        print(f"  Glass color sample: RGB = {v2_rgba[is_glass2][0]}")

# Also check purple Decepticon insignias or yellow accents on V1 & V2
# Yellow accents on V2 wings:
v2_rgb = v2_rgba[:, :, :3]
is_yellow = (v2_rgb[:, :, 0] > 180) & (v2_rgb[:, :, 1] > 180) & (v2_rgb[:, :, 2] < 80)
print(f"V2 yellow wing stripes: {is_yellow.sum():,} ({is_yellow.mean()*100:.3f}%)")
