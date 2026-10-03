import UnityPy
import struct

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
tr_to_go = {}
go_dict = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        tr_to_go[obj.path_id] = go_id

arcee_smr_bones = []
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        bones = tree.get('m_Bones', [])
        if len(bones) == 63:
            for b in bones:
                tr_id = b.get('m_PathID')
                go_id = tr_to_go.get(tr_id)
                arcee_smr_bones.append(go_dict.get(go_id, {}).get('m_Name'))
            break

print(f"Arcee SMR bones count: {len(arcee_smr_bones)}")
for i, b in enumerate(arcee_smr_bones):
    print(f"  {i}: {b}")
