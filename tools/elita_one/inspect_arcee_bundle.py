import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

print("Objects in Arcee bundle:")
for obj in env.objects:
    if obj.type.name in ["AnimationClip", "GameObject", "Mesh"]:
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", str(data)))
        print(f"[{obj.type.name}] {name}")
