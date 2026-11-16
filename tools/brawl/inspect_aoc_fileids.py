import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

meg_bundle = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(meg_bundle)

# Also check m_ExternalReferences of the serialized file
for f in env.files.values():
    if hasattr(f, "header"):
        pass

aoc = [o for o in env.objects if o.type.name == "AnimatorOverrideController" and o.path_id == -8652027754329276107][0]
tt = aoc.read_typetree()
for c in tt.get("m_Clips", [])[:10]:
    orig = c.get("m_OriginalClip")
    over = c.get("m_OverrideClip")
    print(f"Orig: {orig} -> Over: {over}")
