import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Texture2D':
        tree = obj.read_typetree()
        print(f"Texture2D {obj.path_id}: '{tree.get('m_Name')}' ({tree.get('m_Width')}x{tree.get('m_Height')}) format={tree.get('m_TextureFormat')}")
