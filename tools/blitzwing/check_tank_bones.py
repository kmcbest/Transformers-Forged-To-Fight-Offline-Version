import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.path_id == 2138194849323017337:
        smr = o.read_typetree()
        root_bone = smr.get("m_RootBone", {}).get("m_PathID")
        bones = [b.get("m_PathID") for b in smr.get("m_Bones", [])]
        print(f"Tank SMR RootBone PID: {root_bone}")
        root_go = obj_map[root_bone].read_typetree().get("m_GameObject", {}).get("m_PathID") if root_bone in obj_map else 0
        root_name = obj_map[root_go].read_typetree().get("m_Name") if root_go in obj_map else "Unknown"
        print(f"Tank RootBone GO: '{root_name}'")
        for i, b_id in enumerate(bones[:5]):
            b_go = obj_map[b_id].read_typetree().get("m_GameObject", {}).get("m_PathID") if b_id in obj_map else 0
            b_name = obj_map[b_go].read_typetree().get("m_Name") if b_go in obj_map else "Unknown"
            print(f"  Bone[{i}] PID={b_id}: '{b_name}'")
