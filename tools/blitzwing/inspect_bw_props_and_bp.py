import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

MEGA_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
BW_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
WB_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\windblade_gs_odr\windblade_gs.assetbundle")
MM_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\motormaster_gs_voyager2015_odr\motormaster_gs_voyager2015.assetbundle")

for label, path in [("MEGATRON", MEGA_BUNDLE), ("WINDBLADE", WB_BUNDLE), ("MOTORMASTER", MM_BUNDLE)]:
    env = UnityPy.load(str(path))
    objs = {o.path_id: o for o in env.objects}
    print(f"\n=== {label} PropsController ===")
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            t = o.read_typetree()
            if "_props" in t:
                go = objs[t["m_GameObject"]["m_PathID"]].read_typetree()
                print(f"  GO={go['m_Name']} PID={o.path_id}")
                for k, v in zip(t["_props"]["_serializedKeys"], t["_props"]["_serializedValues"]):
                    print(f"    key={k} Name={v['Name']} InitFlags={v['InitFlags']} Root='{v['RootPath']}' Pos={v['PositionOffset']} Rot={v['RotationOffset']} inst={v['_instance']['m_PathID']} anim={v['_animator']['m_PathID']}")

# Also inspect Blitzwing Robot SMR BindPoses + Unity LeftHand/RightHand palm verts in unity space!
bw_env = UnityPy.load(str(BW_BUNDLE))
bw_objs = {o.path_id: o for o in bw_env.objects}
print("\n=== BLITZWING Robot Mesh BindPose for LeftHand/RightHand ===")
for o in bw_env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        s = o.read_typetree()
        if s["m_Mesh"]["m_PathID"] == -8866497113587093232:  # MESH_ROBOT_PID
            bones = [b["m_PathID"] for b in s["m_Bones"]]
            m_tt = bw_objs[s["m_Mesh"]["m_PathID"]].read_typetree()
            for bn in ("LeftHand", "RightHand"):
                for i, bp_id in enumerate(bones):
                    b_go = bw_objs[bw_objs[bp_id].read_typetree()["m_GameObject"]["m_PathID"]].read_typetree()
                    if b_go["m_Name"] == bn:
                        bp = m_tt["m_BindPose"][i]
                        print(f"  {bn} idx={i} bp_row0={[round(bp[k],4) for k in ('e00','e01','e02','e03')]}")
                        print(f"             bp_row1={[round(bp[k],4) for k in ('e10','e11','e12','e13')]}")
                        print(f"             bp_row2={[round(bp[k],4) for k in ('e20','e21','e22','e23')]}")
                        break
            break
