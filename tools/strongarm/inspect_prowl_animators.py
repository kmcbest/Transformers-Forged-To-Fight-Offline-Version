import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name in ["AnimatorController", "AnimatorOverrideController"]:
        data = obj.read()
        print(f"Animator: {data.m_Name} (type={obj.type.name})")
        if hasattr(data, "m_AnimationClips"):
            print(f"  m_AnimationClips: {[c.read().m_Name for c in data.m_AnimationClips if c]}")
        if hasattr(data, "m_Clips"):
            print(f"  m_Clips: {len(data.m_Clips)}")
