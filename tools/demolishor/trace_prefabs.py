import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# Map transform to gameobject
tr_to_go = {}
go_to_tr = {}
go_dict = {}
smr_dict = {}

for obj in env.objects:
    if obj.type.name == 'GameObject':
        tree = obj.read_typetree()
        go_dict[obj.path_id] = tree
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        tr_to_go[obj.path_id] = go_id
        go_to_tr[go_id] = obj.path_id
    elif obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        smr_dict[go_id] = tree

# Find root GameObjects
def trace_hierarchy(go_id, depth=0):
    go = go_dict.get(go_id)
    if not go:
        return
    name = go.get('m_Name')
    smr_info = ""
    if go_id in smr_dict:
        smr = smr_dict[go_id]
        mesh_id = smr.get('m_Mesh', {}).get('m_PathID')
        smr_info = f" [SMR: Mesh PathID={mesh_id}, Bones={len(smr.get('m_Bones', []))}]"
    print("  " * depth + f"- {name} (GO PathID={go_id}){smr_info}")
    
    tr_id = go_to_tr.get(go_id)
    if tr_id:
        for obj in env.objects:
            if obj.path_id == tr_id:
                tr = obj.read_typetree()
                for child_ptr in tr.get('m_Children', []):
                    c_tr_id = child_ptr.get('m_PathID')
                    c_go_id = tr_to_go.get(c_tr_id)
                    trace_hierarchy(c_go_id, depth + 1)

print("=== Tracing ironhide_cin_rotf.prefab (8887288183430146843) ===")
trace_hierarchy(8887288183430146843)

print("\n=== Tracing ironhide_cin_rotf_lw.prefab (-4129943903446534184) ===")
trace_hierarchy(-4129943903446534184)
