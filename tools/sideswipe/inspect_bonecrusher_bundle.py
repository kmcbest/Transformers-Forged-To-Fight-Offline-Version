import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\bonecrusher_cin_rotf_odr\bonecrusher_cin_rotf.assetbundle")
env = UnityPy.load(str(p))

print(f"=== AnimationClips in {p.name} ===")
for o in env.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        print(f"  Clip: {tt.get('m_Name')} (pid={o.path_id})")

for o in env.objects:
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"  AOC: {tt.get('m_Name')} (pid={o.path_id})")
        for cl in tt.get("m_Clips", []):
            orig = cl.get("m_OriginalClip", {})
            over = cl.get("m_OverrideClip", {})
            print(f"    orig={orig.get('m_PathID')} -> over={over.get('m_PathID')}")
