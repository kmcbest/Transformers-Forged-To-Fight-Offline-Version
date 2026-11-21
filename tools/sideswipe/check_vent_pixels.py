import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

DIFF_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_Diffuse.png")
RAOE_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures\cha_sideswipe_main_RAOE.png")

diff = np.array(Image.open(DIFF_PATH))
raoe = np.array(Image.open(RAOE_PATH))

print(f"Left Chest Vent at (X=635, Y=901):")
print(f"  Diffuse RGB: {diff[901, 635]}")
print(f"  RAOE: R={raoe[901, 635, 0]}, A={raoe[901, 635, 1]}, E={raoe[901, 635, 2]}")

print(f"Right Chest Vent at (X=911, Y=901):")
print(f"  Diffuse RGB: {diff[901, 911]}")
print(f"  RAOE: R={raoe[901, 911, 0]}, A={raoe[901, 911, 1]}, E={raoe[901, 911, 2]}")
