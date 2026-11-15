import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

rj_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(rj_bundle))
obj_map = {o.path_id: o for o in env.objects}

# Get transform PID 555161202889287211
ctr = obj_map[555161202889287211].read_typetree()
for ch in ctr["m_Children"]:
    ch_tr = obj_map[ch["m_PathID"]].read_typetree()
    ch_go = obj_map[ch_tr["m_GameObject"]["m_PathID"]].read_typetree()
    print("Child GO:", ch_go["m_Name"], "Transform PID:", ch["m_PathID"])
    # check its children
    for sub in ch_tr["m_Children"]:
        sub_tr = obj_map[sub["m_PathID"]].read_typetree()
        sub_go = obj_map[sub_tr["m_GameObject"]["m_PathID"]].read_typetree()
        print("  Sub Child GO:", sub_go["m_Name"])
