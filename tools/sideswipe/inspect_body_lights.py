import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

p = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\textures\Body_Lights.png")
im = Image.open(p).convert("RGBA")
arr = np.array(im)
print(f"Body_Lights: shape={arr.shape}")
print(f"Unique colors (RGB): {len(np.unique(arr.reshape(-1, 4)[:, :3], axis=0))}")
unique_colors = np.unique(arr.reshape(-1, 4), axis=0)
for c in unique_colors[:10]:
    print(f"  RGBA: {c}")
