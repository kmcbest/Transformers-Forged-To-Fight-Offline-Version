import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
env = UnityPy.load(str(bundle_path))
for obj in env.objects:
    if obj.type.name == "AnimationClip" and obj.path_id == 6507922945028023628:
        tt = obj.read_typetree()
        print("Clip name:", tt.get("m_Name"))
        print("Muscle clip:", "m_MuscleClip" in tt)
        rot_curves = tt.get("m_RotationCurves", [])
        print("Rotation curves count:", len(rot_curves))
        if rot_curves:
            print("First 5 paths:", [c.get("path") for c in rot_curves[:5]])
        # check m_MuscleClip
        mc = tt.get("m_MuscleClip", {})
        clip_data = mc.get("m_ClipData", {})
        print("MuscleClip curves count:", len(clip_data.get("m_ConstantCurves", [])) + len(clip_data.get("m_DenseClip", {}).get("m_SampleArray", [])))
