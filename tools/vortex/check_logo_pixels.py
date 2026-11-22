import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image

logo = np.array(Image.open('e:/Agent/TFTF-blender/tools/vortex/DecepticonLogo.png'))
print("Shape:", logo.shape)
print("Unique alpha values:", np.unique(logo[:, :, 3]))
# let's see RGB on opaque pixels
opaque = logo[:, :, 3] > 0
print("Opaque count:", opaque.sum())
print("Mean RGB on opaque:", logo[opaque, :3].mean(axis=0))
print("Mean RGB on transparent:", logo[~opaque, :3].mean(axis=0))
