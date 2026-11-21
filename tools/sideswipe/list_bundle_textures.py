import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bp = Path(r"E:\Agent\TFTF-blender\assets_redeco\sideswipe_cin_rotf.assetbundle")
env = UnityPy.load(str(bp))

print("Texture2D objects in sideswipe_cin_rotf.assetbundle:")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        name = getattr(data, 'm_Name', 'unnamed')
        print(f"  PathID {obj.path_id}: '{name}', size={data.m_Width}x{data.m_Height}, fmt={data.m_TextureFormat}")
