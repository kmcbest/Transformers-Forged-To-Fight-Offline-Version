import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
tr_to_name = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        tree = obj.read_typetree()
        tr_id = None
        for comp in tree.get('m_Components', []):
            if 'Transform' in comp.get('component', {}):
                pass
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        # find gameobject name
        tr_to_name[obj.path_id] = go_id

go_names = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        tree = obj.read_typetree()
        go_names[obj.path_id] = tree.get('m_Name')

for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        if len(tree.get('m_Bones', [])) == 25:
            bones = [go_names.get(tr_to_name.get(b.get('m_PathID'))) for b in tree.get('m_Bones', [])]
            print("25 Bones of SMR:", bones)
            break
