import UnityPy

env = UnityPy.load("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
for obj in env.objects:
    if obj.type.name == "Material":
        data = obj.read()
        print(f"Material: {data.m_Name}")
        for p in data.m_SavedProperties.m_Floats:
            if p[0] in ["_Mode", "_ZWrite", "_SrcBlend", "_DstBlend", "_Cutoff"]:
                print(f"  {p[0]} = {p[1]}")
        print("  Shader path_id:", data.m_Shader.path_id)
