import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Animator":
        anim = obj.read()
        go = anim.m_GameObject.read()
        if go.m_Name == "transformed":
            print(f"Animator on {go.m_Name}:")
            print(f"  Avatar: {anim.m_Avatar.read().m_Name if anim.m_Avatar.path_id != 0 else 'None'}")
            print(f"  Controller: {anim.m_Controller.read().m_Name if anim.m_Controller.path_id != 0 else 'None'}")
            print(f"  CullingMode: {anim.m_CullingMode}")
