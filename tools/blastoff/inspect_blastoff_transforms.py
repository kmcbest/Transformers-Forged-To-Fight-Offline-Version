import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\assets_redeco\blastoff_gs.assetbundle")
env = UnityPy.load(str(p))
obj_map = {o.path_id: o for o in env.objects}

root_tr = obj_map[6377849924665476503].read_typetree()
children = root_tr.get("m_Children", [])
print("Root transform children for lw:")
for ch in children:
    ch_obj = obj_map.get(ch.get("m_PathID"))
    if ch_obj:
        ch_tr = ch_obj.read_typetree()
        go_pptr = ch_tr.get("m_GameObject", {})
        go_obj = obj_map.get(go_pptr.get("m_PathID"))
        go_name = go_obj.read_typetree().get("m_Name") if go_obj else "unknown"
        print(f"  Child: {go_name} (PID: {ch.get('m_PathID')})")
        print(f"    scale: {ch_tr.get('m_LocalScale')}")
        print(f"    pos: {ch_tr.get('m_LocalPosition')}")
        print(f"    children count: {len(ch_tr.get('m_Children', []))}")
        for c2 in ch_tr.get("m_Children", []):
            c2_obj = obj_map.get(c2.get("m_PathID"))
            if c2_obj:
                c2_tr = c2_obj.read_typetree()
                c2_go = obj_map.get(c2_tr.get("m_GameObject", {}).get("m_PathID"))
                c2_name = c2_go.read_typetree().get("m_Name") if c2_go else "unknown"
                print(f"    SubChild: {c2_name} (PID: {c2.get('m_PathID')})")
