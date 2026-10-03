import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        if mesh.m_Name == "cha_arcee_gs_deluxe2014_01":
            print(f"=== Mesh: {mesh.m_Name} ===")
            print(f"Vertex count: {mesh.m_VertexData.m_VertexCount}")
            print(f"Submeshes count: {len(mesh.m_SubMeshes)}")
            for idx, sm in enumerate(mesh.m_SubMeshes):
                print(f"  Submesh {idx}: indexCount={sm.indexCount}, firstByte={sm.firstByte}")
            print(f"Bindposes count: {len(mesh.m_BindPose)}")
            print(f"BoneHash count: {len(mesh.m_BoneNameHashes)}")
            # Check bone weights
            weights = mesh.m_Skin
            print(f"Skin count: {len(weights)}")
            break
