import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name in ["AnimatorController", "AnimatorOverrideController"]:
        ctrl = obj.read()
        print(f"Controller: {ctrl.m_Name} (type: {obj.type.name})")
        if "car" in ctrl.m_Name.lower():
            # list clips or states
            if hasattr(ctrl, "m_AnimationClips"):
                for c in ctrl.m_AnimationClips:
                    print(f"  Clip ptr: {c.read().m_Name if c.path_id != 0 else 'None'}")
