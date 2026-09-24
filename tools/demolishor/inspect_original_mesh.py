import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            bindposes = tree.get('m_BindPose', [])
            print(f"cha_ironhide_cin_rotf_00 has {len(bindposes)} bindposes.")
            skin = tree.get('m_Skin', [])
            print(f"Skin count: {len(skin)}")
            aabb = tree.get('m_LocalAABB', {})
            print(f"LocalAABB: {aabb}")

