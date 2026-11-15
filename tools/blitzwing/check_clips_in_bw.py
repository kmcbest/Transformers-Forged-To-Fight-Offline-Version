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

for pid in (-1178808270879590806, 639328769293232052, -6735820901998650, -5900093419524027639):
    if pid in obj_map:
        tt = obj_map[pid].read_typetree()
        print(f"Found clip {pid}: '{tt.get('m_Name')}'")
    else:
        print(f"MISSING clip {pid}!")
