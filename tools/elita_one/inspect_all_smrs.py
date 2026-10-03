import UnityPy

bundle_path = 'assets_redeco/elita_one_gs.assetbundle'
env = UnityPy.load(bundle_path)

# Let's inspect GameObjects, Components, SMRs, Animators for Prefab 1 and Prefab 2
go_dict = {}
tr_to_go = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        tr_to_go[obj.path_id] = go_id

# Let's check all SMRs in the bundle and what Mesh PathID they use
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        smr = obj.read_typetree()
        go_id = smr.get('m_GameObject', {}).get('m_PathID')
        go_name = go_dict.get(go_id, {}).get('m_Name')
        mesh_pid = smr.get('m_Mesh', {}).get('m_PathID')
        mats = [m.get('m_PathID') for m in smr.get('m_Materials', [])]
        root_bone = smr.get('m_RootBone', {}).get('m_PathID')
        print(f"SMR on '{go_name}' (PID {obj.path_id}):")
        print(f"  Mesh PID: {mesh_pid}")
        print(f"  Materials: {mats}")
        print(f"  RootBone: {root_bone}")
        print(f"  Bones count: {len(smr.get('m_Bones', []))}")
