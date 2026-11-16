import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

mesh_asset = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle")
env = UnityPy.load(str(mesh_asset))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        if "00" in tt['m_Name']:
            print(f"Mesh: {tt['m_Name']}")
            print(f"Bones count: {len(tt['m_BoneNameHashes'])}")
            for idx, baabb in enumerate(tt['m_BonesAABB']):
                min_pt = baabb['m_Min']
                max_pt = baabb['m_Max']
                if idx in [8, 11, 12, 13, 14, 15, 19, 20, 21, 22, 35]:
                    print(f"  Bone {idx:2d} AABB: min=({min_pt['x']:.2f}, {min_pt['y']:.2f}, {min_pt['z']:.2f}) max=({max_pt['x']:.2f}, {max_pt['y']:.2f}, {max_pt['z']:.2f})")
