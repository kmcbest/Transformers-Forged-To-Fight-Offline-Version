import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        smr = obj.read_typetree()
        if len(smr.get('m_Bones', [])) == 25:
            print(f"Vehicle SMR: {obj.path_id}")
            print(f"  Materials: {smr.get('m_Materials')}")
            print(f"  RootBone: {smr.get('m_RootBone')}")
            print(f"  Mesh: {smr.get('m_Mesh')}")
