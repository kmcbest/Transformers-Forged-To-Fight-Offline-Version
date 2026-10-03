import UnityPy

c_env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in c_env.objects:
    if obj.type.name == 'Mesh' and obj.read_typetree().get('m_Name') == 'cha_elita_one_vehicle_grafted':
        tree = obj.read_typetree()
        submeshes = tree.get('m_SubMeshes', [])
        for i, sm in enumerate(submeshes):
            print(f"Submesh {i}: firstVertex={sm['firstVertex']}, vertexCount={sm['vertexCount']}")
