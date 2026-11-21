import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\sideswipe_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

print(f"=== Inspecting Materials & SMRs in {bundle_path.name} ===")
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        go_name = "unknown"
        mats = [mp.get("m_PathID") for mp in tt.get("m_Materials", [])]
        print(f"SMR {o.path_id}: enabled={tt.get('m_Enabled')}, mats={mats}, mesh={tt.get('m_Mesh')}")

for o in env.objects:
    if o.type.name == "Material":
        tt = o.read_typetree()
        print(f"Material {o.path_id}: name={tt.get('m_Name')}")
        cols = {k: v for k, v in tt.get("m_SavedProperties", {}).get("m_Colors", [])}
        if "_Color" in cols:
            print(f"  _Color={cols['_Color']}")
