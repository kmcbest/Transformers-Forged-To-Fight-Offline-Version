import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        if "attackSpecial_03" in data.m_Name:
            print(f"=== Clip: {data.m_Name} (length: {data.m_MuscleClip.m_StopTime if hasattr(data, 'm_MuscleClip') else 'unknown'}) ===")
