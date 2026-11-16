import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        data = obj.read()
        name = getattr(data, 'm_Name', '')
        if "01" in name:
            print(f"Mesh: {name}")
            bps = data.m_BindPose
            print(f"  Bindposes count: {len(bps)}")
            for idx in range(len(bps)):
                bp = bps[idx]
                mat = np.array([
                    [bp.e00, bp.e01, bp.e02, bp.e03],
                    [bp.e10, bp.e11, bp.e12, bp.e13],
                    [bp.e20, bp.e21, bp.e22, bp.e23],
                    [bp.e30, bp.e31, bp.e32, bp.e33],
                ])
                inv = np.linalg.inv(mat)
                pos = inv[:3, 3]
                print(f"  BP[{idx:2d}] pos: ({pos[0]:7.3f}, {pos[1]:7.3f}, {pos[2]:7.3f})")
