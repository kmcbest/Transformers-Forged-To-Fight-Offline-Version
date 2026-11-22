import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np
from pathlib import Path

TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\02_textures")
raoe = Image.open(TEX_DIR / "cha_blastoff_main_RAOE.png")
arr = np.array(raoe)

print(f"RAOE shape: {arr.shape}")
r = arr[:, :, 0]
g = arr[:, :, 1]
b = arr[:, :, 2]

print(f"R (Roughness?) min={r.min()}, max={r.max()}, mean={r.mean():.2f}")
print(f"G (AO?) min={g.min()}, max={g.max()}, mean={g.mean():.2f}")
print(f"B (Emissive Mask!) min={b.min()}, max={b.max()}, mean={b.mean():.2f}")

# Where is B > 50?
lit_y, lit_x = np.where(b > 50)
print(f"Pixels with B > 50: {len(lit_y)}")
if len(lit_y) > 0:
    print(f"B lit bounding box: X=[{lit_x.min()}, {lit_x.max()}], Y=[{lit_y.min()}, {lit_y.max()}]")

# Now let's check where the eye visor UV coordinates are on cha_blastoff_main!
