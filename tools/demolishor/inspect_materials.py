import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == 'Material':
        tree = obj.read_typetree()
        name = tree.get('m_Name')
        shader = tree.get('m_Shader', {})
        print(f"\nMaterial '{name}' (PathID {obj.path_id}):")
        tex_envs = tree.get('m_SavedProperties', {}).get('m_TexEnvs', [])
        for tex in tex_envs:
            prop_name = tex[0]
            val = tex[1]
            tex_ptr = val.get('m_Texture', {})
            print(f"  Prop '{prop_name}': Texture PathID {tex_ptr.get('m_PathID')}")

