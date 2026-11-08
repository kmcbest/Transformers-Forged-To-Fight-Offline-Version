import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as R

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

# Local rotation of RotorMain from inspect_rotormain_transform.py:
# LocalRot: {'x': 0.03084351308643818, 'y': 0.7064337134361267, 'z': 0.706433892250061, 'w': 0.030843807384371758}
q_local_rotormain = [0.03084351308643818, 0.7064337134361267, 0.706433892250061, 0.030843807384371758]
r_base = R.from_quat(q_local_rotormain)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read_typetree()
        if data.get("m_Name") == "frontend_Grindor_levelup_vehicle_idle_transformed":
            mc = data.get("m_MuscleClip", {})
            dc = mc.get("m_Clip", {}).get("data", {}).get("m_DenseClip", {})
            samples = dc.get("m_SampleArray", [])
            for fi in [0, 5, 10, 15, 20]:
                q_anim = samples[fi*8 : fi*8 + 4]
                # In Mecanim, animated rotation is relative or absolute local rotation
                r_anim = R.from_quat(q_anim)
                # World rotation: r_base * r_anim or r_anim
                euler_anim = r_anim.as_euler('xyz', degrees=True)
                euler_world = (r_base * r_anim).as_euler('xyz', degrees=True)
                print(f"Frame {fi:2d}: anim euler: {euler_anim.round(1)} | combined euler: {euler_world.round(1)}")
