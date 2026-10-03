import UnityPy

env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh' and obj.read_typetree().get('m_Name') == 'cha_elita_one_vehicle_grafted':
        tree = obj.read_typetree()
        print("LocalAABB:", tree.get('m_LocalAABB'))
