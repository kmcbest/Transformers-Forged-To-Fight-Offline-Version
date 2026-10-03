import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AssetBundle":
        ab = obj.read()
        print("AssetBundle name:", ab.m_Name)
        for k, v in ab.m_Container:
            target = v.asset.read()
            print(f"  Container entry: '{k}' -> type {target.type if hasattr(target, 'type') else type(target).__name__}, name {getattr(target, 'm_Name', getattr(target, 'name', 'unnamed'))}")
