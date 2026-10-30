import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_curr = Path(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")
env_curr = UnityPy.load(str(bundle_curr))

for obj in env_curr.objects:
    if obj.type.name == "Material":
        t = obj.read_typetree()
        print(f"Material {obj.path_id}: {t.get('m_Name')}, Shader: {t.get('m_Shader')}")
        for tex in t.get('m_SavedProperties', {}).get('m_TexEnvs', []):
            print(f"   Tex: {tex}")
