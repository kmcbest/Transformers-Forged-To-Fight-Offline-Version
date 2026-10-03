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

for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        m_pid = tree.get('m_Mesh', {}).get('m_PathID')
        bones = tree.get('m_Bones', [])
        if len(bones) == 25:
            print(f"Vehicle SMR PID {obj.path_id}:")
            for i, b in enumerate(bones):
                tr_id = b.get('m_PathID')
                go_id = tr_to_go.get(tr_id)
                print(f"  Bone {i}: {go_dict.get(go_id, {}).get('m_Name')}")
            break
