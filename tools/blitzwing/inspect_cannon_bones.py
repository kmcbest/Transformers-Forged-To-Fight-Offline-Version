import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

for pid in (-7481134504555158405, 3992037002325232027):
    smr = obj_map[pid].read_typetree()
    print(f"SMR {pid}:")
    print("  RootBone:", smr.get("m_RootBone"))
    print("  Bones count:", len(smr.get("m_Bones", [])))
    for b in smr.get("m_Bones", []):
        b_obj = obj_map.get(b["m_PathID"])
        if b_obj:
            b_tt = b_obj.read_typetree()
            go_pid = b_tt.get("m_GameObject", {}).get("m_PathID")
            go_name = obj_map[go_pid].read_typetree().get("m_Name") if go_pid in obj_map else ""
            print(f"    Bone: PID={b['m_PathID']} GO Name='{go_name}'")
