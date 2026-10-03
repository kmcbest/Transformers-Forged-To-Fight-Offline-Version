import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        mesh_pid = tree.get('m_Mesh', {}).get('m_PathID')
        bones = tree.get('m_Bones', [])
        name = tree.get('m_GameObject', {}).get('m_PathID')
        print(f"SMR PID {obj.path_id}: bones={len(bones)}, mesh_pid={mesh_pid}")
