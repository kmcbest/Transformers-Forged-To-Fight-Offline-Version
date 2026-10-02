import UnityPy

bpath = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bpath)

print("Texture2D in arcee bundle:")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        print(f"  Texture2D: {tree.get('m_Name')} (PathID: {obj.path_id}, width: {tree.get('m_Width')}, height: {tree.get('m_Height')})")
