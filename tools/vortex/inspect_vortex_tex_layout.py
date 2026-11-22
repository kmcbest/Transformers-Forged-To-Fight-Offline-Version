import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image

diff = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\dumped_vortex_tex\tform_misc_A.png"))
print("Shape:", diff.shape)
# check alpha or transparent pixels
if diff.shape[2] == 4:
    alpha = diff[:, :, 3]
    print("Min alpha:", alpha.min(), "Max alpha:", alpha.max(), "Zero alpha count:", (alpha == 0).sum())

# Let's inspect what is in vh_vortexbase_mat.jpg from the zip!
import zipfile
import io
with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    vh_mat = Image.open(io.BytesIO(z.read("textures/vh_vortexbase_mat.jpg")))
    print("vh_vortexbase_mat.jpg size:", vh_mat.size)
    vh_mat.save(r"e:\Agent\TFTF-blender\tools\vortex\vh_vortexbase_mat.png")
