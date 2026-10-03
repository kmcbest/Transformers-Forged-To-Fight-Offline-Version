import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
tr_to_go = {}
go_names = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_names[obj.path_id] = obj.read_typetree().get('m_Name')
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_to_go[obj.path_id] = tree.get('m_GameObject', {}).get('m_PathID')

for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        if len(tree.get('m_Bones', [])) == 63:
            bones = [go_names.get(tr_to_go.get(b.get('m_PathID'))) for b in tree.get('m_Bones', [])]
            print(f"SMR {obj.path_id}: first 5 bones: {bones[:5]}")
            print(f"  all bones: {bones}")
