import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

for name in ["Body", "Legs", "Hands", "Tank", "Jet", "Treads"]:
    p = Path(rf"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Textures\{name}_Diffuse.png")
    im = Image.open(p).convert("RGB")
    arr = np.array(im, dtype=np.float32)
    # calculate saturation: (max(R,G,B) - min(R,G,B)) / max(R,G,B)
    mx = np.max(arr, axis=2)
    mn = np.min(arr, axis=2)
    diff = mx - mn
    sat = np.zeros_like(mx)
    mask = mx > 10
    sat[mask] = diff[mask] / mx[mask]
    
    # Neutral grey metal: low saturation (< 0.20) and medium/dark brightness (30 < mx < 180)
    # Painted purple/yellow/red: high saturation (sat >= 0.20) or white (mx >= 180)
    is_metal = (sat < 0.22) & (mx > 25) & (mx < 190)
    if name == "Treads":
        is_metal = np.ones_like(mx, dtype=bool)
    
    metal_ratio = np.mean(is_metal)
    print(f"{name:8s}: metal ratio={metal_ratio:.2%}, mean sat={np.mean(sat):.2f}")
