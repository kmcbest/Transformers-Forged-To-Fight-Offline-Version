import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from PIL import Image
import numpy as np

for name in ['Body_Diffuse.png', 'Hands_Diffuse.png', 'Legs_Diffuse.png']:
    p = f'E:/Agent/TFTF-blender/toolchain/unity_build_project/Assets/Blitzwing/Textures/{name}'
    im = Image.open(p)
    arr = np.array(im)
    print(f"{name}: size={im.size}, mode={im.mode}, mean_rgb={arr[:,:,:3].mean(axis=(0,1))}")
