import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image

crop = np.array(Image.open('e:/Agent/TFTF-blender/tools/vortex/crop_door_uv.png'))
print("Shape:", crop.shape)
print("Mean RGB:", crop.mean(axis=(0, 1)))
print("Min RGB:", crop.min(axis=(0, 1)))
print("Max RGB:", crop.max(axis=(0, 1)))
