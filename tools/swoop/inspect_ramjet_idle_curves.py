import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", ""))
        if name == "Ramjet_Normal_idle01":
            print(f"AnimationClip: {name}")
            # print all curve paths
            for curve in getattr(data, "m_RotationCurves", []):
                print(f"  Rot: {curve.path}")
            for curve in getattr(data, "m_PositionCurves", []):
                print(f"  Pos: {curve.path}")
