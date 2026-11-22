import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\assets_redeco\blastoff_gs.assetbundle")
env = UnityPy.load(str(p))
obj_map = {o.path_id: o for o in env.objects}

def print_tree(tr_pid, depth=0):
    tr_obj = obj_map.get(tr_pid)
    if not tr_obj: return
    tr = tr_obj.read_typetree()
    go_pptr = tr.get("m_GameObject", {})
    go = obj_map.get(go_pptr.get("m_PathID"))
    gname = go.read_typetree().get("m_Name") if go else "unknown"
    scl = tr.get("m_LocalScale")
    pos = tr.get("m_LocalPosition")
    print("  " * depth + f"- {gname} (Tr PID: {tr_pid}, GO PID: {go_pptr.get('m_PathID')}) scl=({scl['x']:.2f},{scl['y']:.2f},{scl['z']:.2f}) pos=({pos['x']:.2f},{pos['y']:.2f},{pos['z']:.2f})")
    for ch in tr.get("m_Children", []):
        ch_pid = ch.get("m_PathID")
        # only recurse if not deep in bone tree
        if depth < 3:
            print_tree(ch_pid, depth + 1)

print("=== Blastoff_GS Transform Hierarchy ===")
print_tree(3076213683770163573, 0)
