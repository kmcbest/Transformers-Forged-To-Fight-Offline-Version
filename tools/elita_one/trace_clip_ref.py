import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

target_path_id = None
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        if data.m_Name == "Arcee_Normal_attackSpecial_03_transformed":
            target_path_id = obj.path_id
            print(f"Found clip path_id: {target_path_id}")
            break

# Now search which objects reference this path_id
for obj in env.objects:
    raw = obj.get_raw_data()
    # Check if target_path_id is in references
    # UnityPy can inspect references
    data = obj.read()
    if obj.type.name in ["AnimatorOverrideController", "AnimatorController", "GameObject"]:
        name = getattr(data, "m_Name", getattr(data, "name", "unnamed"))
        # Check if references target_path_id
        if hasattr(data, "m_Clips"):
            for c in data.m_Clips:
                if c.m_OverrideClip.path_id == target_path_id:
                    print(f"Referenced by {obj.type.name}: {name}")
