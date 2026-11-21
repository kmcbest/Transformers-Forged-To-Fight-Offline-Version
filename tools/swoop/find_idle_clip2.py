import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

for p in [Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle"),
          Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")]:
    env = UnityPy.load(str(p))
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            data = obj.read()
            name = getattr(data, "m_Name", "")
            if name == "ramjet_gs_deluxe2008_idle01":
                print(f"Found {name} in {p.name}")
                # Print animated paths
                for c in getattr(data, "m_RotationCurves", []):
                    if "shoulder" in c.path.lower() or "arm" in c.path.lower():
                        print(f"  Rot: {c.path}")
                for c in getattr(data, "m_PositionCurves", []):
                    if "shoulder" in c.path.lower() or "arm" in c.path.lower():
                        print(f"  Pos: {c.path}")
