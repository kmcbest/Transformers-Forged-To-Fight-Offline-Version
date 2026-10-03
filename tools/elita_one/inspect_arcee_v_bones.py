import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        go = smr.m_GameObject.read()
        if smr.m_Mesh.path_id != 0 and smr.m_Mesh.read().m_Name == "cha_arcee_gs_deluxe2014_01":
            print(f"SMR GO: {go.m_Name}")
            print(f"RootBone: {smr.m_RootBone.read().m_GameObject.read().m_Name if smr.m_RootBone.path_id != 0 else 'None'}")
            print(f"Bones count: {len(smr.m_Bones)}")
            for idx, b_ptr in enumerate(smr.m_Bones):
                b_go = b_ptr.read().m_GameObject.read()
                print(f"  [{idx}] {b_go.m_Name}")
            break
