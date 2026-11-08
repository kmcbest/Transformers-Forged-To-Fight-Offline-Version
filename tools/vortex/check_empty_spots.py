import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

img = Image.open(r"E:\Agent\TFTF-blender\3rd-party-models\vortex\processed_textures\cha_vortex_main_a.png")
arr = np.array(img)
print("Image shape:", arr.shape)

# Check head slot: (1024..1536, 1536..2048)
# In head slot, rb_vortex_head_mat is 512x512
# What about wep slot: (1536..2048, 1536..2048)?
# In wep slot, wep.jpg has black areas.
# But what if we inspect the weapon UVs?
# Where in UV [0..1, 0..1] does wep.jpg actually have polygons?
