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
            mc = data.get("m_MuscleClip", {})
            dc = mc.get("m_Clip", {}).get("data", {}).get("m_DenseClip", {})
            print("DenseClip:")
            print("  m_FrameCount:", dc.get("m_FrameCount"))
            print("  m_CurveCount:", dc.get("m_CurveCount"))
            print("  m_SampleRate:", dc.get("m_SampleRate"))
            print("  m_BeginTime:", dc.get("m_BeginTime"))
            samples = dc.get("m_SampleArray", [])
            print(f"  First 32 samples: {samples[:32]}")
