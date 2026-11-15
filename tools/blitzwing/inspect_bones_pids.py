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

for pid in (9041275945456695869, 4936350875999462921):
    tr = obj_map[pid].read_typetree()
    go_pid = tr["m_GameObject"]["m_PathID"]
    go = obj_map[go_pid].read_typetree()
    print(f"Bone PID {pid}: GO='{go.get('m_Name')}' pos={tr.get('m_LocalPosition')} rot={tr.get('m_LocalRotation')}")
