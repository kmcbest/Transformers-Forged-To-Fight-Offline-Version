import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

meg_bundle = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(meg_bundle)

clip_names = {}
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tt = obj.read_typetree()
        clip_names[obj.path_id] = tt.get("m_Name")

aoc = [o for o in env.objects if o.type.name == "AnimatorOverrideController" and o.path_id == -8652027754329276107][0]
tt = aoc.read_typetree()
print("Clips in override_Megatron_Cin_ROTF_fight:")
for c in tt.get("m_Clips", []):
    orig = c.get("m_OriginalClip", {}).get("m_PathID")
    over = c.get("m_OverrideClip", {}).get("m_PathID")
    orig_n = clip_names.get(orig, f"Ext_{orig}")
    over_n = clip_names.get(over, f"Ext_{over}")
    print(f"  Orig: {orig_n:<45} -> Over: {over_n}")
