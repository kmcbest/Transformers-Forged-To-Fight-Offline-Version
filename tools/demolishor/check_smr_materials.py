import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        mesh_id = tree.get('m_Mesh', {}).get('m_PathID')
        materials = tree.get('m_Materials', [])
        print(f"SMR PathID: {obj.path_id}, GO PathID: {go_id}, Mesh PathID: {mesh_id}")
        print(f"  Materials count: {len(materials)}, Materials: {materials}")

