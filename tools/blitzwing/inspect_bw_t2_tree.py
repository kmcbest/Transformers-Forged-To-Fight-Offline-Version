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

# Combat transformed_2 instance PID: -2922891105374208445
inst_go = obj_map[-2922891105374208445].read_typetree()
print("Combat transformed_2 GO components:", inst_go.get("m_Component"))
for c in inst_go.get("m_Component", []):
    c_pid = c['component']['m_PathID']
    c_obj = obj_map[c_pid]
    if c_obj.type.name == "Transform":
        tr = c_obj.read_typetree()
        print(f"Transform {c_pid} children count: {len(tr.get('m_Children', []))}")
        for ch in tr.get("m_Children", []):
            ch_tr = obj_map[ch['m_PathID']].read_typetree()
            ch_go = obj_map[ch_tr['m_GameObject']['m_PathID']].read_typetree()
            print(f"  Child {ch['m_PathID']}: '{ch_go['m_Name']}'")
            for sub_ch in ch_tr.get("m_Children", []):
                sub_tr = obj_map[sub_ch['m_PathID']].read_typetree()
                sub_go = obj_map[sub_tr['m_GameObject']['m_PathID']].read_typetree()
                print(f"    Sub-Child {sub_ch['m_PathID']}: '{sub_go['m_Name']}'")
