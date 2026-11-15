import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {o.path_id: o for o in env.objects}

print("=== CHECKING MATERIALS ===")
for pid in (1722215546450231611, 2588147852330761274):
    if pid in obj_map:
        mat = obj_map[pid].read_typetree()
        print(f"\nMaterial PID {pid}: Name='{mat.get('m_Name')}'")
        print(f"  Shader: {mat.get('m_Shader')}")
        print(f"  SavedProperties: {mat.get('m_SavedProperties', {}).get('m_TexEnvs')}")
        print(f"  Floats: {mat.get('m_SavedProperties', {}).get('m_Floats')}")
        print(f"  Colors: {mat.get('m_SavedProperties', {}).get('m_Colors')}")
