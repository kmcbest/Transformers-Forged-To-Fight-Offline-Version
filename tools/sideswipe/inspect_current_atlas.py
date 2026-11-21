import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np

TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures")

diff_p = TEX_DIR / "cha_sideswipe_main_Diffuse.png"
raoe_p = TEX_DIR / "cha_sideswipe_main_RAOE.png"

diff = np.array(Image.open(diff_p))
raoe = np.array(Image.open(raoe_p))

print(f"Diffuse shape: {diff.shape}, RAOE shape: {raoe.shape}")

# Sample eye region: around (y=1750, x=745) and (y=1750, x=830)
print("\n--- Eye region samples ---")
for y in [1745, 1750, 1755]:
    for x in [745, 788, 830]:
        print(f"y={y}, x={x}: Diffuse={diff[y, x]}, RAOE={raoe[y, x]} (R={raoe[y, x, 0]}, G={raoe[y, x, 1]}, Em={raoe[y, x, 2]})")

# Sample chest headlight region: around (y=900, x=635) and (y=900, x=911)
print("\n--- Chest region samples ---")
for y in [895, 900, 905]:
    for x in [635, 911]:
        print(f"y={y}, x={x}: Diffuse={diff[y, x]}, RAOE={raoe[y, x]} (R={raoe[y, x, 0]}, G={raoe[y, x, 1]}, Em={raoe[y, x, 2]})")

# Check all pixels where Emissive > 50
em = raoe[:, :, 2]
bright_em_indices = np.where(em > 50)
print(f"\nTotal pixels with Emissive > 50: {len(bright_em_indices[0])}")
if len(bright_em_indices[0]) > 0:
    min_y, max_y = np.min(bright_em_indices[0]), np.max(bright_em_indices[0])
    min_x, max_x = np.min(bright_em_indices[1]), np.max(bright_em_indices[1])
    print(f"Emissive bounding box: Y in [{min_y}, {max_y}], X in [{min_x}, {max_x}]")
    # Mean diffuse color of emissive pixels in upper half (eyes) vs lower half (chest)
    eyes_mask = (em > 50) & (np.arange(2048)[:, None] > 1500)
    chest_mask = (em > 50) & (np.arange(2048)[:, None] < 1500)
    print(f"Eyes emissive pixels: {np.count_nonzero(eyes_mask)}")
    if np.count_nonzero(eyes_mask) > 0:
        print(f"Eyes mean diffuse RGB: {diff[eyes_mask].mean(axis=0)}")
    print(f"Chest emissive pixels: {np.count_nonzero(chest_mask)}")
    if np.count_nonzero(chest_mask) > 0:
        print(f"Chest mean diffuse RGB: {diff[chest_mask].mean(axis=0)}")
