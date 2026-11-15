import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

# find Transform -3905281141488939495 ('transformed')
tr_trans = obj_map[-3905281141488939495].read_typetree()
for ch in tr_trans.get("m_Children", []):
    ch_id = ch.get("m_PathID")
    ch_tr = obj_map[ch_id].read_typetree()
    go_id = ch_tr.get("m_GameObject", {}).get("m_PathID")
    go_name = obj_map[go_id].read_typetree().get("m_Name")
    print(f"Child of transformed: PID={ch_id} GO='{go_name}'")
    if go_name == "Reference":
        for gch in ch_tr.get("m_Children", []):
            gch_id = gch.get("m_PathID")
            gch_tr = obj_map[gch_id].read_typetree()
            g_go_id = gch_tr.get("m_GameObject", {}).get("m_PathID")
            g_go_name = obj_map[g_go_id].read_typetree().get("m_Name")
            print(f"  Child of Reference: PID={gch_id} GO='{g_go_name}'")
