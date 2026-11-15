import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

TEX_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Textures")
for name in ["Tank", "Treads", "Jet", "Body"]:
    p = TEX_DIR / f"{name}_Diffuse.png"
    if p.exists():
        im = Image.open(p)
        arr = np.array(im)
        print(f"{name}_Diffuse: size={im.size}, mode={im.mode}, mean_rgb={arr[:,:,:3].mean(axis=(0,1))}")
