import UnityPy

bundle_path = r"d:\Agent\tftf\assets_netflix\cha_ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name in ["Mesh", "GameObject", "SkinnedMeshRenderer"]:
        try:
            data = obj.read()
            name = getattr(data, 'name', getattr(data, 'm_Name', ''))
            print(f"Type: {obj.type.name}, Name: {name}")
        except Exception as e:
            print(f"Type: {obj.type.name}, Err: {e}")
