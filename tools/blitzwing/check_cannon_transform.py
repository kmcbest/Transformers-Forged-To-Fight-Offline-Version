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

for go_pid in (-2446282080136274639, -2922891105374208445):
    go = obj_map[go_pid].read_typetree()
    print(f"GO {go['m_Name']} ({go_pid}):")
    for c in go["m_Component"]:
        comp = obj_map[c["component"]["m_PathID"]]
        if comp.type.name == "Transform":
            tr = comp.read_typetree()
            print("  LocalPosition:", tr.get("m_LocalPosition"))
            print("  LocalRotation:", tr.get("m_LocalRotation"))
            print("  LocalScale:", tr.get("m_LocalScale"))
            parent_pid = tr.get("m_Father", {}).get("m_PathID")
            if parent_pid and parent_pid in obj_map:
                p_go_pid = obj_map[parent_pid].read_typetree()["m_GameObject"]["m_PathID"]
                print(f"  Parent: '{obj_map[p_go_pid].read_typetree()['m_Name']}'")
