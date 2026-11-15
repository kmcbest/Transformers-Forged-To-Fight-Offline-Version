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

pids = [
    -3905281141488939495, -6848276043409792716, -4070916873066828308, -7543220954911659241,
    -6095442020295608261, -6028308954984925732, -3207237225000537856, -7942071043123098758
]
for pid in pids:
    if pid in obj_map:
        tr = obj_map[pid].read_typetree()
        go_pid = tr['m_GameObject']['m_PathID']
        go = obj_map[go_pid].read_typetree()
        print(f"PID {pid}: GO='{go['m_Name']}' parent={tr.get('m_Father')}")
    else:
        print(f"PID {pid} NOT FOUND!")
