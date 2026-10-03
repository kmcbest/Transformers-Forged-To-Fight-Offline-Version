import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        if len(tree.get('m_Bones', [])) == 25:
            print(f"SMR PID {obj.path_id}:")
            mats = tree.get('m_Materials', [])
            print(f"  Materials: {mats}")
            print(f"  AABB: {tree.get('m_AABB')}")
