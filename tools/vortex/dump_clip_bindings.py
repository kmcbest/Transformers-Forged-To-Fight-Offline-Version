import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read_typetree()
        if data.get("m_Name") == "frontend_Grindor_levelup_vehicle_idle_transformed":
            print(f"Clip: {data.get('m_Name')}")
            # Typetree has m_ClipBindingConstant
            cbc = data.get("m_ClipBindingConstant", {})
            bindings = cbc.get("genericBindings", [])
            print(f"Generic bindings count: {len(bindings)}")
            for idx, b in enumerate(bindings):
                print(f"  [{idx}] path_hash={b.get('path')}, attr={b.get('attribute')}, typeID={b.get('typeID')}, isPPtr={b.get('isPPtrCurve')}")
            
            # Check floatCurves or other curves
            fc = data.get("m_FloatCurves", [])
            print(f"Float curves count: {len(fc)}")
            rc = data.get("m_RotationCurves", [])
            print(f"Rotation curves count: {len(rc)}")
            cpc = data.get("m_CompressedRotationCurves", [])
            print(f"Compressed rotation curves count: {len(cpc)}")
            euc = data.get("m_EulerCurves", [])
            print(f"Euler curves count: {len(euc)}")
            posc = data.get("m_PositionCurves", [])
            print(f"Position curves count: {len(posc)}")
            
            # Check MuscleClip
            mc = data.get("m_MuscleClip", {})
            print(f"MuscleClip present: {bool(mc)}")
            if mc:
                print(f"  StartTime: {mc.get('m_StartTime')}, StopTime: {mc.get('m_StopTime')}")
                clip_data = mc.get("m_Clip", {})
                constant_clip = clip_data.get("m_ConstantClip", {})
                dense_clip = clip_data.get("m_DenseClip", {})
                streamed_clip = clip_data.get("m_StreamedClip", {})
                print(f"  ConstantClip count: {len(constant_clip.get('data', [])) if constant_clip else 0}")
                print(f"  DenseClip frameCount: {dense_clip.get('m_FrameCount', 0)}, curveCount: {dense_clip.get('m_CurveCount', 0)}")
                print(f"  StreamedClip curveCount: {streamed_clip.get('m_CurveCount', 0)}")
