import UnityPy

asset_path = r"toolchain/unity_build_project/Assets/ElitaOne/cha_elita_one_vehicle_grafted.asset"
env = UnityPy.load(asset_path)
print(f"Objects in asset: {len(env.objects)}")
for obj in env.objects:
    print(f"  Type: {obj.type.name}, id: {obj.path_id}")
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        print(f"    Name: {tree.get('m_Name')}, verts: {tree.get('m_VertexData', {}).get('m_VertexCount')}")
        print(f"    Submeshes: {len(tree.get('m_SubMeshes', []))}")
        print(f"    Bindposes: {len(tree.get('m_BindPose', []))}")
