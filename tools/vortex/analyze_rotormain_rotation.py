import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read_typetree()
        if data.get("m_Name") == "frontend_Grindor_levelup_vehicle_idle_transformed":
            mc = data.get("m_MuscleClip", {})
            dc = mc.get("m_Clip", {}).get("data", {}).get("m_DenseClip", {})
            samples = dc.get("m_SampleArray", [])
            # 62 frames, 8 curves per frame
            # First 4 curves are RotorMain quaternion (x, y, z, w)
            qs = []
            for f in range(62):
                q = samples[f*8 : f*8 + 4]
                qs.append(q)
            
            print(f"Total frames: {len(qs)}")
            # Print frame 0, 15, 30, 45, 60
            for fi in [0, 15, 30, 45, 60]:
                q = qs[fi]
                # Convert quaternion to euler or axis-angle
                # In Unity: q = (x, y, z, w)
                angle_rad = 2.0 * np.arccos(np.clip(q[3], -1.0, 1.0))
                s = np.sin(angle_rad / 2.0)
                axis = np.array(q[:3]) / s if abs(s) > 1e-5 else np.array([0, 1, 0])
                print(f"Frame {fi:2d}: q=({q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}, {q[3]:.4f}) | angle={np.degrees(angle_rad):.1f}° | axis=({axis[0]:.3f}, {axis[1]:.3f}, {axis[2]:.3f})")
