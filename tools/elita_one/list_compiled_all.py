import UnityPy

c_env = UnityPy.load('toolchain/unity_build_project/AssetBundles/elita_one_mesh.assetbundle')
for obj in c_env.objects:
    print(f"Type: {obj.type.name}, id: {obj.path_id}")
    if obj.type.name in ['Mesh', 'Material', 'Texture2D']:
        tree = obj.read_typetree()
        print(f"   Name: '{tree.get('m_Name')}'")
