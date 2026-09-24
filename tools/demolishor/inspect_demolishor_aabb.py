import UnityPy

env = UnityPy.load(r"d:\Agent\tftf\toolchain\unity_build_project\AssetBundles\demolishor_mesh.assetbundle")

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        print("Mesh Name:", tree.get("m_Name"))
        print("LocalAABB:", tree.get("m_LocalAABB"))
