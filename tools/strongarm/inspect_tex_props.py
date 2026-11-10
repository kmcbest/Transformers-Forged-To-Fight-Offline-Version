import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(p))

for obj in env.objects:
    if obj.type.name == "Texture2D":
        t = obj.read_typetree()
        print(f"Tex '{t.get('m_Name')}' (PID {obj.path_id}): fmt={t.get('m_TextureFormat')}, colorSpace={t.get('m_ColorSpace')}, mips={t.get('m_MipCount')}, size={t.get('m_Width')}x{t.get('m_Height')}")
