import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == 'Texture2D':
        tree = obj.read_typetree()
        print(f"Texture2D '{tree.get('m_Name')}' (PathID {obj.path_id})")
