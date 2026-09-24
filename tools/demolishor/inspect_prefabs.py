import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# Check AssetBundle container
for obj in env.objects:
    if obj.type.name == 'AssetBundle':
        tree = obj.read_typetree()
        print("AssetBundle Container:")
        for item in tree.get('m_Container', []):
            print(f"  {item[0]} -> PathID {item[1]['asset']['m_PathID']}")

    if obj.type.name == 'Prefab':
        tree = obj.read_typetree()
        print("Prefab:", tree.get('m_Name'))
