import UnityPy

bpath = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bpath)

for obj in env.objects:
    if obj.type.name == "Material":
        mat = obj.read()
        name = mat.m_Name
        print(f"\n--- Material: {name} ---")
        tex_envs = mat.m_SavedProperties.m_TexEnvs
        for prop, val in tex_envs:
            tex_ptr = val.m_Texture
            if tex_ptr and tex_ptr.path_id != 0:
                tex_obj = tex_ptr.read()
                print(f"  {prop}: {tex_obj.m_Name} (PathID: {tex_ptr.path_id})")
        floats = mat.m_SavedProperties.m_Floats
        for prop, val in floats:
            if any(k in prop.lower() for k in ["mode", "metallic", "roughness"]):
                print(f"  {prop}: {val}")
