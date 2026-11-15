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
    if o.type.name == "Animator":
        tt = o.read_typetree()
        go_id = tt.get("m_GameObject", {}).get("m_PathID")
        go_name = obj_map[go_id].read_typetree().get("m_Name") if go_id in obj_map else "unknown"
        av_id = tt.get("m_Avatar", {}).get("m_PathID")
        av_name = obj_map[av_id].read_typetree().get("m_Name") if av_id in obj_map else "unknown"
        print(f"Animator on '{go_name}' (PID {o.path_id}): Avatar='{av_name}' (PID {av_id})")
        if av_id in obj_map:
            av_tt = obj_map[av_id].read_typetree()
            tos = av_tt.get("m_TOS", [])
            print(f"  Avatar TOS count: {len(tos)}")
            for t in tos[:10]:
                print(f"    {t}")
