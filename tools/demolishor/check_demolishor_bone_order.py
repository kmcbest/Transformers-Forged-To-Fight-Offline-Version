import UnityPy

env = UnityPy.load(r'd:\Agent\tftf\toolchain\unity_build_project\AssetBundles\demolishor_mesh.assetbundle')

path_to_name = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_ptr = t.get("m_GameObject", {})
        for g_obj in env.objects:
            if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                path_to_name[obj.path_id] = g_obj.read_typetree().get("m_Name")
                break

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read_typetree()
        bones = smr.get("m_Bones", [])
        print("Demolishor SMR bones order in Unity:")
        for idx, b in enumerate(bones[:30]):
            pid = b.get("m_PathID")
            print(f"  [{idx:02d}] {path_to_name.get(pid, 'Unknown')}")
        break
