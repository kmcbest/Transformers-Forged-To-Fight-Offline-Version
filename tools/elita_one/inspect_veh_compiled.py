import UnityPy

env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh' and obj.read_typetree().get('m_Name') == 'cha_elita_one_vehicle_grafted':
        tree = obj.read_typetree()
        print("Vehicle mesh name:", tree.get('m_Name'))
        print("  verts:", tree.get('m_VertexData', {}).get('m_VertexCount'))
        print("  submeshes:", len(tree.get('m_SubMeshes', [])))
        for i, sm in enumerate(tree.get('m_SubMeshes', [])):
            print(f"    Submesh {i}: verts={sm.get('vertexCount')}, indices={sm.get('indexCount')}")
        print("  bindposes:", len(tree.get('m_BindPose', [])))
