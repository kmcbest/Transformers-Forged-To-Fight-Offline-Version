import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

# Build bone name map from Arcee prefab
# First find transformed GameObject and its children
bone_names = []
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        if smr.m_Mesh.path_id != 0 and smr.m_Mesh.read().m_Name == "cha_arcee_gs_deluxe2014_01":
            for b_ptr in smr.m_Bones:
                bone_names.append(b_ptr.read().m_GameObject.read().m_Name)
            break

print("25 vehicle bones:", bone_names)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        if data.m_Name == "Arcee_Normal_attackSpecial_03_transformed":
            print(f"=== Clip: {data.m_Name} ===")
            if hasattr(data, "m_ClipBindingConstant"):
                cbc = data.m_ClipBindingConstant
                # Check curves
                print(f"GenericBindings count: {len(cbc.genericBindings)}")
                # In Unity, path hash is CRC32 of bone path
                # Let's see if we can match any
                import binascii
                # Test hashes
                hash_to_name = {}
                for name in bone_names + ["COG", "Reference", "transformed", "character_model"]:
                    # Unity uses CRC32 or custom hash? Let's check common combinations
                    pass
