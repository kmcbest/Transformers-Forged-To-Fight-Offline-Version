import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image

diff = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_robot_diff.png").convert("RGB"))
sub = diff[1490:1700, 60:350].astype(int)
r, g, b = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]

# Steel blue armor above trim has g > r + 10. Honeycomb purple-indigo has b > r + 15, b > g + 25, and r >= g - 4!
honey_strict = (b > g + 25) & (b > r + 15) & (r >= g - 4) & (b > 65)
print(f"Strict purple honeycomb pixels: {honey_strict.sum()}")

# Save visualization overlay on chest_grille_crop coords [1450..1800, 50..400]
vis = diff[1450:1800, 50:400].copy()
sub_vis = vis[40:250, 10:300]
sub_vis[honey_strict] = [255, 0, 255]
Image.fromarray(vis).save(r"e:\Agent\TFTF-blender\tools\vortex\diag\honey_strict_overlay.png")
print("Saved honey_strict_overlay.png")
