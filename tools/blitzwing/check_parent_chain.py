import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

cur_tid = -3905281141488939495
while cur_tid != 0 and cur_tid in obj_map:
    t_obj = obj_map[cur_tid]
    t = t_obj.read_typetree()
    go_id = t.get("m_GameObject", {}).get("m_PathID")
    go_name = obj_map[go_id].read_typetree().get("m_Name") if go_id in obj_map else "Unknown"
    print(f"Transform {cur_tid} on GO {go_id} ('{go_name}'):")
    print(f"  Pos: {t.get('m_LocalPosition')}")
    print(f"  Rot: {t.get('m_LocalRotation')}")
    print(f"  Scale: {t.get('m_LocalScale')}")
    father = t.get("m_Father", {})
    cur_tid = father.get("m_PathID", 0)
