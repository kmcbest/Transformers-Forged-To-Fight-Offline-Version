import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(bundle))
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tt = obj.read_typetree()
        print(f"AnimationClip: '{tt.get('m_Name')}' (PID={obj.path_id})")
    elif obj.type.name == "AnimatorOverrideController":
        tt = obj.read_typetree()
        print(f"AnimatorOverrideController: '{tt.get('m_Name')}' (PID={obj.path_id})")

