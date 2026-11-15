import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

for pid in (7256209656881810047, -7543220954911659241, 6354873720385821623, -7942071043123098758):
    tr = obj_map[pid].read_typetree()
    go_id = tr.get("m_GameObject", {}).get("m_PathID")
    print(f"Transform {pid} ('{obj_map[go_id].read_typetree().get('m_Name')}'):")
    print(f"  Pos: {tr.get('m_LocalPosition')}")
    print(f"  Rot: {tr.get('m_LocalRotation')}")
    print(f"  Scale: {tr.get('m_LocalScale')}")
