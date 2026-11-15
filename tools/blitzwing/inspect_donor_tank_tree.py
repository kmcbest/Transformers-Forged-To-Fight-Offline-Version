import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_bundle))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        if tt["m_Name"] in ("transformed", "cha_megatron_gs_leader2015_01", "COG"):
            print(f"GO {tt['m_Name']} (PID {o.path_id}): active={tt['m_IsActive']}")
            for c in tt["m_Component"]:
                cid = c["component"]["m_PathID"]
                if cid in obj_map and obj_map[cid].type.name == "Transform":
                    ctr = obj_map[cid].read_typetree()
                    father_pid = ctr["m_Father"]["m_PathID"]
                    children_pids = [ch["m_PathID"] for ch in ctr["m_Children"]]
                    father_name = obj_map[father_pid].read_typetree().get("m_Name") if father_pid in obj_map else "unknown"
                    print(f"  Transform PID {cid}: father={father_pid} ({father_name}), children={len(children_pids)}")
                    print(f"    pos={ctr['m_LocalPosition']}, rot={ctr['m_LocalRotation']}, scale={ctr['m_LocalScale']}")
