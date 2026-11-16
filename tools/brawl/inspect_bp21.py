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
            bp21 = data.m_BindPose[21]
            mat = np.array([
                [bp21.e00, bp21.e01, bp21.e02, bp21.e03],
                [bp21.e10, bp21.e11, bp21.e12, bp21.e13],
                [bp21.e20, bp21.e21, bp21.e22, bp21.e23],
                [bp21.e30, bp21.e31, bp21.e32, bp21.e33],
            ])
            print("BP[21] matrix:\n", mat)
