import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from PIL import Image

env = UnityPy.load('assets_redeco/vortex_gs.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        tt = obj.read_typetree()
        name = tt.get('m_Name')
        if 'wpns' in name:
            img = obj.read().image
            print(f"Texture: {name}, size: {img.size}")
            img.save(f"e:/Agent/TFTF-blender/tools/vortex/{name}.png")
