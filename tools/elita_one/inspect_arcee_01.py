import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            print("Name:", tree.get('m_Name'))
            submeshes = tree.get('m_SubMeshes', [])
            for i, sm in enumerate(submeshes):
                print(f"  Submesh {i}: firstVertex={sm.get('firstVertex')}, vertexCount={sm.get('vertexCount')}, indexCount={sm.get('indexCount')}")
