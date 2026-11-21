import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {obj.path_id: obj for obj in env.objects}

def print_tree(go_pid, indent=0):
    go_obj = obj_map.get(go_pid)
    if not go_obj:
        return
    d = go_obj.read_typetree()
    name = d.get("m_Name", "")
    print(" " * indent + f"- {name} (PID: {go_pid})")
    
    # find Transform component
    for c in d.get("m_Component", []):
        cid = c.get("component", {}).get("m_PathID")
        c_obj = obj_map.get(cid)
        if c_obj and c_obj.type.name == "Transform":
            td = c_obj.read_typetree()
            for ch in td.get("m_Children", []):
                ch_tr = obj_map.get(ch.get("m_PathID"))
                if ch_tr:
                    ch_go_id = ch_tr.read_typetree().get("m_GameObject", {}).get("m_PathID")
                    print_tree(ch_go_id, indent + 2)

print_tree(2724871595904881499)
