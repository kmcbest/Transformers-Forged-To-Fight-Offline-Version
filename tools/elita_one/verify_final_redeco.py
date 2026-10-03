import UnityPy

env = UnityPy.load('assets_redeco/elita_one_gs.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        print(f"Mesh: {obj.path_id} name='{tree.get('m_Name')}' verts={tree.get('m_VertexData', {}).get('m_VertexCount')}")
    elif obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        if len(tree.get('m_Bones', [])) == 25:
            print(f"Vehicle SMR: {obj.path_id} mesh_pid={tree.get('m_Mesh', {}).get('m_PathID')} mats={tree.get('m_Materials')}")
