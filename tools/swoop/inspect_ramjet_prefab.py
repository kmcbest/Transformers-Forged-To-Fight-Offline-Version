import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))
sf = env.file

obj_map = {obj.path_id: obj for obj in env.objects}

for obj in env.objects:
    if obj.type.name == "GameObject" and obj.path_id == 1529847556182042256:
        d = obj.read_typetree()
        print("Ramjet_GS_Deluxe2008 GameObject:")
        print("m_Name:", d.get("m_Name"))
        print("m_Component count:", len(d.get("m_Component", [])))
        for c in d.get("m_Component", []):
            cid = c.get("component", {}).get("m_PathID")
            c_obj = obj_map.get(cid)
            if c_obj:
                print("  Component:", c_obj.type.name, "PID:", cid)
                if c_obj.type.name == "Transform":
                    td = c_obj.read_typetree()
                    print("  Transform children count:", len(td.get("m_Children", [])))
                    for ch in td.get("m_Children", []):
                        ch_tr = obj_map.get(ch.get("m_PathID"))
                        if ch_tr:
                            ch_go = obj_map.get(ch_tr.read_typetree().get("m_GameObject", {}).get("m_PathID"))
                            if ch_go:
                                print("    Child:", ch_go.read_typetree().get("m_Name"), "PID:", ch_go.path_id)
        break
