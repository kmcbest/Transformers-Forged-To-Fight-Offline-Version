import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        go_name = smr.m_GameObject.read().m_Name
        if "00" in go_name and not "wpns" in go_name:
            print(f"SMR: {go_name}")
            bones = [b.read().m_GameObject.read().m_Name for b in smr.m_Bones]
            mesh = smr.m_Mesh.read()
            for i, bname in enumerate(bones):
                bp = mesh.m_BindPose[i]
                mat = np.array([
                    [bp.e00, bp.e01, bp.e02, bp.e03],
                    [bp.e10, bp.e11, bp.e12, bp.e13],
                    [bp.e20, bp.e21, bp.e22, bp.e23],
                    [bp.e30, bp.e31, bp.e32, bp.e33]
                ])
                inv = np.linalg.inv(mat)
                pos = inv[:3, 3]
                if any(k in bname for k in ["Arm", "Shoulder", "Leg", "Head", "Spine"]):
                    print(f"  Bone [{i:2d}] {bname:15s}: pos = ({pos[0]:6.3f}, {pos[1]:6.3f}, {pos[2]:6.3f})")
            break
