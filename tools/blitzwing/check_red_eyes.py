import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

p = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Textures\Body_Diffuse.png")
im = Image.open(p)
arr = np.array(im)

# Find high-red pixels: R > 150, G < 60, B < 60
red_mask = (arr[:, :, 0] > 160) & (arr[:, :, 1] < 70) & (arr[:, :, 2] < 70)
print(f"Red pixels count in Body_Diffuse: {np.sum(red_mask)}")
