import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

# Jet SMR in combat: 3992037002325232027
smr = obj_map[3992037002325232027].read_typetree()
go_id = smr["m_GameObject"]["m_PathID"]

cur_tid = 0
for c in obj_map[go_id].read_typetree().get("m_Component", []):
    cid = c.get("component", {}).get("m_PathID")
    if cid in obj_map and obj_map[cid].type.name == "Transform":
        cur_tid = cid
        break

while cur_tid != 0 and cur_tid in obj_map:
    tr = obj_map[cur_tid].read_typetree()
    g_id = tr.get("m_GameObject", {}).get("m_PathID")
    g_name = obj_map[g_id].read_typetree().get("m_Name") if g_id in obj_map else "Unknown"
    print(f"Transform {cur_tid} GO '{g_name}':")
    print(f"  Pos: {tr.get('m_LocalPosition')}")
    print(f"  Rot: {tr.get('m_LocalRotation')}")
    print(f"  Scale: {tr.get('m_LocalScale')}")
    cur_tid = tr.get("m_Father", {}).get("m_PathID", 0)
