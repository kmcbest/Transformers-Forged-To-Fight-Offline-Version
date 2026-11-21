import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import json

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
env = UnityPy.load(str(bundle_path))
for obj in env.objects:
    if obj.type.name == "AnimationClip" and obj.path_id == 6507922945028023628:
        tt = obj.read_typetree()
        print("Clip keys:", list(tt.keys()))
        mc = tt.get("m_MuscleClip", {})
        print("MuscleClip keys:", list(mc.keys()))
        print("ClipBindingConstant:", list(tt.get("m_ClipBindingConstant", {}).keys()))
