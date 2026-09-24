import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        name = tree.get('m_Name')
        vcount = tree.get('m_VertexData', {}).get('m_VertexCount')
        submeshes = tree.get('m_SubMeshes', [])
        print(f"Mesh '{name}': {vcount} vertices, {len(submeshes)} submeshes")

for obj in env.objects:
    if obj.type.name == 'GameObject':
        tree = obj.read_typetree()
        name = tree.get('m_Name')
        if '00' in name or '01' in name or 'ironhide' in name:
            print(f"GO: {name}, active={tree.get('m_IsActive')}")
