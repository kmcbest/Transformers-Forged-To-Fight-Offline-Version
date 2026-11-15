import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

for pid in (-7481134504555158405, 3992037002325232027):
    smr = obj_map[pid].read_typetree()
    root_b = smr.get("m_RootBone", {}).get("m_PathID")
    print(f"Jet SMR {pid} m_RootBone: {root_b}")
    for b in smr.get("m_Bones", []):
        bid = b.get("m_PathID")
        tr = obj_map[bid].read_typetree() if bid in obj_map else {}
        g_id = tr.get("m_GameObject", {}).get("m_PathID")
        g_name = obj_map[g_id].read_typetree().get("m_Name") if g_id in obj_map else "Unknown"
        print(f"  Bone PID={bid} GO='{g_name}' Pos={tr.get('m_LocalPosition')}")
