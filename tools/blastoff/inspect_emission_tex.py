import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np
from pathlib import Path

TEX_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\BlastOff\02_textures")

diff = Image.open(TEX_DIR / "cha_blastoff_main_Diffuse.png")
emis = Image.open(TEX_DIR / "cha_blastoff_main_Emission.png")
raoe = Image.open(TEX_DIR / "cha_blastoff_main_RAOE.png")

diff_arr = np.array(diff)
emis_arr = np.array(emis)
raoe_arr = np.array(raoe)

print(f"Diffuse size: {diff.size}, mode: {diff.mode}")
print(f"Emission size: {emis.size}, mode: {emis.mode}")
print(f"RAOE size: {raoe.size}, mode: {raoe.mode}")

# Find where Emission > 30
if len(emis_arr.shape) == 3:
    emis_val = emis_arr[:, :, :3].max(axis=2)
else:
    emis_val = emis_arr

lit_y, lit_x = np.where(emis_val > 50)
print(f"Number of lit pixels in Emission: {len(lit_y)}")
if len(lit_y) > 0:
    print(f"Lit bounds: X=[{lit_x.min()}, {lit_x.max()}], Y=[{lit_y.min()}, {lit_y.max()}]")

# In RAOE, Blue is AO, Green is Roughness/Metallic, Alpha/Red is what?
# In Kabam PBR:
# R = Roughness (or Reflectance?)
# A = AO?
# G = ???
# B = Emission?
# Let's check what channels mean in Kabam RAOE!
