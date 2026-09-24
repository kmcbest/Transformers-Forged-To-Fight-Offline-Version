import numpy as np
import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            bindposes = tree.get('m_BindPose', [])
            print(f"Found {len(bindposes)} bindposes.")
            for idx in [18, 19, 21, 27, 28, 29, 65, 14, 58]:
                # bindpose is 4x4 matrix dict: e00, e01, ..., e33
                bp = bindposes[idx]
                mat = np.array([
                    [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
                    [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
                    [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
                    [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
                ])
                inv_mat = np.linalg.inv(mat)
                pos = inv_mat[:3, 3]
                print(f"Bone {idx}: World Pos = ({pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f})")
