import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

donor_path = Path("E:/Agent/TFTF/assets_ios/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

for pid in (-7543220954911659241, -7942071043123098758):
    tr = obj_map[pid].read_typetree()
    children = tr.get("m_Children", [])
    print(f"PID {pid} children count: {len(children)}")
    for c in children:
        c_tr = obj_map[c['m_PathID']].read_typetree()
        c_go = obj_map[c_tr['m_GameObject']['m_PathID']].read_typetree()
        print(f"  Child PID {c['m_PathID']}: '{c_go['m_Name']}'")
