import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        mesh = obj.read()
        if mesh.m_Name == "cha_arcee_gs_deluxe2014_01":
            print(f"=== {mesh.m_Name} ===")
            print(dir(mesh.m_BindPose[0]))
            bp = mesh.m_BindPose[0]
            print(f"e03={getattr(bp, 'e03', None)}, e13={getattr(bp, 'e13', None)}, e23={getattr(bp, 'e23', None)}")
            print(f"m03={getattr(bp, 'm03', None)}, m13={getattr(bp, 'm13', None)}, m23={getattr(bp, 'm23', None)}")
            break
