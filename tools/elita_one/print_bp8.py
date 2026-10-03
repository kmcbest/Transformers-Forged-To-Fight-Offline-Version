import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            bps = tree.get('m_BindPose', [])
            print("Bindpose 8 (chop1_interior_center_hidden):")
            bp8 = bps[8]
            for row in range(4):
                print(f"  [{bp8[f'e{row}0']:.4f}, {bp8[f'e{row}1']:.4f}, {bp8[f'e{row}2']:.4f}, {bp8[f'e{row}3']:.4f}]")
            break
