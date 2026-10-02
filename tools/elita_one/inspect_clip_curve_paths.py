import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if name in ["TeamSelect_Agile_idle", "agile_normal_attackLight_01_jab_R"]:
            print(f"=== Clip: {name} ===")
            # Check curve paths
            if hasattr(data, 'm_FloatCurves'):
                print(f"  FloatCurves count: {len(data.m_FloatCurves)}")
            if hasattr(data, 'm_PositionCurves'):
                print(f"  PositionCurves count: {len(data.m_PositionCurves)}")
                for pc in data.m_PositionCurves[:5]:
                    print(f"    pos path: '{pc.path}'")
            if hasattr(data, 'm_RotationCurves'):
                print(f"  RotationCurves count: {len(data.m_RotationCurves)}")
                for rc in data.m_RotationCurves[:10]:
                    print(f"    rot path: '{rc.path}'")
            if hasattr(data, 'm_CompressedRotationCurves'):
                print(f"  CompressedRotationCurves count: {len(data.m_CompressedRotationCurves)}")
                for crc in data.m_CompressedRotationCurves[:10]:
                    print(f"    comp rot path: '{crc.m_Path}'")
            if hasattr(data, 'm_EulerCurves'):
                print(f"  EulerCurves count: {len(data.m_EulerCurves)}")
            if hasattr(data, 'm_Clip'):
                stream = data.m_Clip
                print(f"  Clip data: stream info, has bindings?")
