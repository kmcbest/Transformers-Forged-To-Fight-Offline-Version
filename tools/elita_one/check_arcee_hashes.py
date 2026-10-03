import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_00':
            hashes = tree.get('m_BoneNameHashes', [])
            print(f"Arcee Mesh 00: {len(hashes)} bone hashes")
            print(f"Bindposes: {len(tree.get('m_BindPose', []))}")
            # print first 10 hashes
            print(hashes[:10])
            break
