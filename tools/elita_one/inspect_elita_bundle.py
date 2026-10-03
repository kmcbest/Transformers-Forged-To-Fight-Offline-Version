import UnityPy

env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        print(f"Mesh: {tree.get('m_Name')}, verts: {tree.get('m_VertexData', {}).get('m_VertexCount')}")
