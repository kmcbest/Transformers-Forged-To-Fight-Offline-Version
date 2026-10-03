import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Material':
        tree = obj.read_typetree()
        print(f"Material {obj.path_id}: '{tree.get('m_Name')}'")
        props = tree.get('m_SavedProperties', {}).get('m_TexEnvs', [])
        for k, v in props:
            t_id = v.get('m_Texture', {}).get('m_PathID')
            print(f"   prop {k} -> {t_id}")
