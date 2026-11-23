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

ma_t = np.array(Image.open(SRC_DIR / "H_shandian_G1_M_a_T.png").convert("RGB"))
# Visor is vivid red
is_red = (ma_t[:, :, 0] > 160) & (ma_t[:, :, 1] < 70) & (ma_t[:, :, 2] < 70)
print(f"M_a red visor pixels: {is_red.sum():,} ({is_red.mean()*100:.3f}%)")

# Check V1 (Tank) red cockpit
v1_t = np.array(Image.open(SRC_DIR / "H_shandian_G1_V1_T.png").convert("RGB"))
v1_red = (v1_t[:, :, 0] > 150) & (v1_t[:, :, 1] < 60) & (v1_t[:, :, 2] < 60)
print(f"V1 (Tank) red canopy pixels: {v1_red.sum():,} ({v1_red.mean()*100:.3f}%)")

# Check V2 (Jet) red cockpit
v2_t = np.array(Image.open(SRC_DIR / "H_shandian_G1_V2_T.png").convert("RGB"))
v2_red = (v2_t[:, :, 0] > 150) & (v2_t[:, :, 1] < 60) & (v2_t[:, :, 2] < 60)
print(f"V2 (Jet) red canopy pixels: {v2_red.sum():,} ({v2_red.mean()*100:.3f}%)")
