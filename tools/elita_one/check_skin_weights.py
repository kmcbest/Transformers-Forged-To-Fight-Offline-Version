import UnityPy
import struct

env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        name = tree.get('m_Name')
        if name == 'cha_elita_one_grafted':
            print(f"=== {name} ===")
            print(f"BindPoses count: {len(tree.get('m_BindPose', []))}")
            print(f"BoneNameHashes: {len(tree.get('m_BoneNameHashes', []))}")
            # Check bone weights sample
            skin = tree.get('m_Skin', [])
            print(f"Skin count: {len(skin)}")
            if skin:
                for i in range(5):
                    print(f"  v{i}: {skin[i]}")
            break
