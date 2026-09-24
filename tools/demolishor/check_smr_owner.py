import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read_typetree()
        if smr.get("m_Mesh", {}).get("m_PathID") == 243592621990493584:
            root_bone = smr.get("m_RootBone", {}).get("m_PathID")
            print(f"SMR PathID: {obj.path_id}")
            print(f"  RootBone PathID: {root_bone}")
            if root_bone == 8843156868773920433:
                print("  -> Belongs to Prefab 1 (Showcase)")
            elif root_bone == -4517635356816119144:
                print("  -> Belongs to Prefab 2 (Combat _lw)")
