import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

target_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mesh_ptr = tree.get("m_Mesh", {})
        for m_obj in env.objects:
            if m_obj.path_id == mesh_ptr.get("m_PathID") and m_obj.type.name == "Mesh":
                if m_obj.read_typetree().get("m_Name") == "cha_ironhide_cin_rotf_00":
                    target_smr = tree
                    break
        if target_smr:
            break

path_to_name = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_ptr = t.get("m_GameObject", {})
        for g_obj in env.objects:
            if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                path_to_name[obj.path_id] = g_obj.read_typetree().get("m_Name")
                break

bones_ptrs = target_smr.get("m_Bones", [])
print(f"Total bones: {len(bones_ptrs)}")
for idx, b_ptr in enumerate(bones_ptrs):
    pid = b_ptr.get("m_PathID")
    name = path_to_name.get(pid, f"Unknown_{pid}")
    print(f"{idx}: '{name}'")
