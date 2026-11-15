import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

# SMR_JET_PIDS = (-7481134504555158405, 3992037002325232027)
for pid in (-7481134504555158405, 3992037002325232027):
    smr = obj_map[pid].read_typetree()
    go_id = smr["m_GameObject"]["m_PathID"]
    go = obj_map[go_id].read_typetree()
    print(f"SMR {pid} is on GO '{go.get('m_Name')}' (PID={go_id})")
    # find transform
    for c in go.get("m_Component", []):
        cid = c.get("component", {}).get("m_PathID")
        if cid in obj_map and obj_map[cid].type.name == "Transform":
            tr = obj_map[cid].read_typetree()
            father = tr.get("m_Father", {}).get("m_PathID")
            f_go = obj_map[father].read_typetree().get("m_GameObject", {}).get("m_PathID") if father in obj_map else 0
            f_name = obj_map[f_go].read_typetree().get("m_Name") if f_go in obj_map else "Unknown"
            print(f"  Transform parent: PID={father} GO='{f_name}'")
