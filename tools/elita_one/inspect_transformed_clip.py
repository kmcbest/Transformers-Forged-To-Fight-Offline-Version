import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        if data.m_Name == "Arcee_Normal_attackSpecial_03_transformed":
            print(f"=== Clip: {data.m_Name} ===")
            # Check curve paths
            for curve in getattr(data, "m_AnimationCurves", []):
                print(f"  AnimCurve path: {curve.path}")
            if hasattr(data, "m_ClipBindingConstant"):
                cbc = data.m_ClipBindingConstant
                for b in cbc.genericBindings:
                    print(f"  GenericBinding: path_hash={b.path}, attribute={b.attribute}, classID={b.classID}")
            break
