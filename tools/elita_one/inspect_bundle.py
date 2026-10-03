import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        print(f"Mesh: {obj.path_id} name='{tree.get('m_Name')}' vertices={tree.get('m_VertexData', {}).get('m_VertexCount')} submeshes={len(tree.get('m_SubMeshes', []))}")
    elif obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        mesh_pid = tree.get('m_Mesh', {}).get('m_PathID')
        print(f"SMR: {obj.path_id} bones={len(tree.get('m_Bones', []))} mesh_pid={mesh_pid}")
