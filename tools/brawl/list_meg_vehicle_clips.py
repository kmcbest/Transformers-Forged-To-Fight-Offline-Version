import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'm_Name', '')
        if "veh" in name.lower() or "trans" in name.lower() or "idle" in name.lower():
            print(f"AnimationClip: {name} (length={d.m_MuscleClip.m_StopTime if hasattr(d, 'm_MuscleClip') else '?'})")
