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
        bones = [b.get("m_PathID") for b in smr.get("m_Bones", [])]
        for i, b_id in enumerate(bones):
            b_go = obj_map[b_id].read_typetree().get("m_GameObject", {}).get("m_PathID") if b_id in obj_map else 0
            b_name = obj_map[b_go].read_typetree().get("m_Name") if b_go in obj_map else "Unknown"
            print(f"Bone[{i:2d}] PID={b_id}: '{b_name}'")

for o in env.objects:
    if o.path_id == 8396146535644667895:
        m = o.read_typetree()
        bp = m["m_BindPose"]
        print(f"Megatron Tank Mesh BindPoses ({len(bp)}):")
        for i in (0, 20):
            print(f"  BP[{i}]:")
            for row in ("e00", "e10", "e20", "e30"):
                print(f"    {row}: {bp[i].get(row)} e01={bp[i].get('e01')} e02={bp[i].get('e02')} e03={bp[i].get('e03')}")
