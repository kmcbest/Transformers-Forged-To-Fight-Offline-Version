import UnityPy

# 1. Load Demolishor to get bone order
d_env = UnityPy.load(r'd:\Agent\tftf\toolchain\unity_build_project\AssetBundles\demolishor_mesh.assetbundle')
d_path_to_name = {}
for obj in d_env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_ptr = t.get("m_GameObject", {})
        for g_obj in d_env.objects:
            if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                d_path_to_name[obj.path_id] = g_obj.read_typetree().get("m_Name")
                break

demolishor_bones = []
for obj in d_env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read_typetree()
        for b in smr.get("m_Bones", []):
            name = d_path_to_name.get(b.get("m_PathID"))
            demolishor_bones.append(name)
        break

print(f"Demolishor has {len(demolishor_bones)} bones in order.")

# 2. Load Ironhide to get name to PathID mapping
i_env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# We need the humanoid combat prefab's transforms, NOT the vehicle transformed ones
# Let's map humanoid transform PathIDs
i_name_to_path = {}
for obj in i_env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_ptr = t.get("m_GameObject", {})
        for g_obj in i_env.objects:
            if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                gname = g_obj.read_typetree().get("m_Name")
                # Don't overwrite humanoid bones with vehicle bones
                if "chop" not in gname and gname not in i_name_to_path:
                    i_name_to_path[gname] = obj.path_id
                break

# Check mapping
missing = []
for bname in demolishor_bones:
    if bname not in i_name_to_path:
        missing.append(bname)

print(f"Mapped {len(demolishor_bones) - len(missing)} / {len(demolishor_bones)} bones.")
if missing:
    print("Missing bones in Ironhide:", missing)
else:
    print("[✓] ALL 80 BONES MATCH PERFECTLY TO IRONHIDE!")
