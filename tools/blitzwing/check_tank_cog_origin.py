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
    if pid in obj_map:
        tr = obj_map[pid].read_typetree()
        go = obj_map[tr['m_GameObject']['m_PathID']].read_typetree()
        print(f"PID {pid}: GO='{go['m_Name']}' parent={tr.get('m_Father')}")
