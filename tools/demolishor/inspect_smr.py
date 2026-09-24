import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
smr_to_go = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        tree = obj.read_typetree()
        go_name = tree.get('m_Name')
        for comp in tree.get('m_Component', []):
            comp_ptr = comp.get('component', {})
            smr_to_go[comp_ptr.get('m_PathID')] = go_name

for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        mesh_ptr = tree.get('m_Mesh', {})
        go_name = smr_to_go.get(obj.path_id, 'UNKNOWN')
        print(f"SMR on GO [{go_name}], SMR PathID {obj.path_id}: Mesh PathID {mesh_ptr.get('m_PathID')}, Bones={len(tree.get('m_Bones', []))}")
