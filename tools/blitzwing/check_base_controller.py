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

if 341294063036995988 in obj_map:
    o = obj_map[341294063036995988]
    print(f"Object {o.path_id} type: {o.type.name}")
    tt = o.read_typetree()
    print("Name:", tt.get("m_Name"))
else:
    print("Not found in bundle!")
