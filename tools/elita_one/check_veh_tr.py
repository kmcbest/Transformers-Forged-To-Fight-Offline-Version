import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')

tr_to_go = {}
go_dict = {}
tr_dict = {}

for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_dict[obj.path_id] = tree
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        tr_to_go[obj.path_id] = go_id

for tr_id, tr in tr_dict.items():
    go_id = tr_to_go.get(tr_id)
    go = go_dict.get(go_id, {})
    name = go.get('m_Name')
    if name in ['transformed', 'COG', 'chop1_interior_center_hidden']:
        pos = tr.get('m_LocalPosition')
        rot = tr.get('m_LocalRotation')
        scale = tr.get('m_LocalScale')
        print(f"Transform '{name}':")
        print(f"  LocalPos: {pos}")
        print(f"  LocalRot: {rot}")
        print(f"  LocalScale: {scale}")
