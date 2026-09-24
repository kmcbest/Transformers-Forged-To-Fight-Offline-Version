import UnityPy

env = UnityPy.load(r"d:\Agent\tftf\toolchain\unity_build_project\AssetBundles\demolishor_mesh.assetbundle")

for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        print(f"Material name: {tree.get('m_Name')}")
        print(f"Shader ptr: {tree.get('m_Shader')}")
        print(f"SavedProperties: {list(tree.get('m_SavedProperties', {}).keys())}")
    elif obj.type.name == "Shader":
        tree = obj.read_typetree()
        print(f"Shader name: {tree.get('m_ParsedForm', {}).get('m_Name', tree.get('m_Name'))}")
    elif obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        print(f"SMR Bones count: {len(tree.get('m_Bones', []))}")
        print(f"SMR Mesh: {tree.get('m_Mesh')}")
        print(f"SMR Materials: {tree.get('m_Materials')}")
