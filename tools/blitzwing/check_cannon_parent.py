import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

for pid in (-464464231220373427, -1893245760279338324):
    tr = obj_map[pid].read_typetree()
    go_id = tr.get("m_GameObject", {}).get("m_PathID")
    go = obj_map[go_id].read_typetree()
    father = tr.get("m_Father", {}).get("m_PathID")
    f_go = obj_map[father].read_typetree().get("m_GameObject", {}).get("m_PathID") if father in obj_map else 0
    f_name = obj_map[f_go].read_typetree().get("m_Name") if f_go in obj_map else "Unknown"
    print(f"GO '{go.get('m_Name')}' (PID={pid}): Parent PID={father} GO='{f_name}' Pos={tr.get('m_LocalPosition')} Rot={tr.get('m_LocalRotation')}")
