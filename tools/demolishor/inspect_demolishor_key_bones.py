import UnityPy
import numpy as np

env = UnityPy.load(r'd:\Agent\tftf\toolchain\unity_build_project\AssetBundles\demolishor_mesh.assetbundle')

for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        aabb = tree.get('m_LocalAABB')
        print("Demolishor LocalAABB:")
        print("  Center:", aabb.get('m_Center'))
        print("  Extent:", aabb.get('m_Extent'))
        
        bps = tree.get('m_BindPose')
        bones_to_check = {
            18: "Hips",
            19: "Spine",
            21: "Spine1",
            28: "Head",
            29: "RightArm",
            65: "LeftArm",
            8:  "RightLeg",
            15: "LeftLeg",
            6:  "RightFoot",
            7:  "LeftFoot"
        }
        print("\nDemolishor Bone Positions in Mesh Space:")
        for idx, name in bones_to_check.items():
            bp = bps[idx]
            mat = np.array([
                [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
                [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
                [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
                [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
            ])
            inv_mat = np.linalg.inv(mat)
            pos = inv_mat[:3, 3]
            print(f"  {name:10s} (bone {idx:02d}): X={pos[0]:6.2f}, Y={pos[1]:6.2f}, Z={pos[2]:6.2f}")
