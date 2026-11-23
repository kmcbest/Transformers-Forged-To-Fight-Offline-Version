import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

MEG_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(MEG_BUNDLE))

for o in env.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        cname = tt.get("m_Name", "")
        if "idle" in cname.lower() or "heavy" in cname.lower():
            print(f"=== AnimationClip '{cname}' ===")
            curves = tt.get("m_RotationCurves", [])
            euler_curves = tt.get("m_EulerCurves", [])
            print(f"  rotation curves count: {len(curves)}, euler curves count: {len(euler_curves)}")
            for rc in curves[:10]:
                print(f"  curve path: {rc.get('path')}")
            break
