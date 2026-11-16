import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

meg_bundle = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(meg_bundle)

for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        print(f"\nAOC: {name} (PID={obj.path_id})")
        clips = tt.get("m_Clips", [])
        print(f"Total overrides: {len(clips)}")
        for c in clips:
            orig = c.get("m_OriginalClip", {}).get("m_PathID")
            over = c.get("m_OverrideClip", {}).get("m_PathID")
            print(f"  Orig PID={orig} -> Over PID={over}")
