import UnityPy

bpath = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bpath)

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        for o2 in env.objects:
            if o2.path_id == go_id:
                go_name = o2.read_typetree().get("m_Name")
                if "00" in go_name:
                    print(f"SMR GameObject: {go_name} (SMR PathID: {obj.path_id})")
                    print(f"  Materials: {tree.get('m_Materials')}")
                    print(f"  Mesh: {tree.get('m_Mesh')}")
                    print(f"  Bones count: {len(tree.get('m_Bones', []))}")
                    print(f"  RootBone: {tree.get('m_RootBone')}")
