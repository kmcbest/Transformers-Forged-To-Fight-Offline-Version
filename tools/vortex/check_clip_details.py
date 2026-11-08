import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle")
if not p_bundle.exists():
    p_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")

env = UnityPy.load(str(p_bundle))

# In frontend_Grindor_levelup_vehicle_idle_transformed
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        c_name = tree.get("m_Name", "")
        if c_name == "frontend_Grindor_levelup_vehicle_idle_transformed":
            clip_bytes = tree.get("m_ClipBindingConstant", {})
            print(f"Generic bindings: {len(clip_bytes.get('genericBindings', []))}")
            # Check pptrCurveMapping
            print(f"pptr curves: {len(clip_bytes.get('pptrCurveMapping', []))}")
            # Check sample animation curves if any
            ac = obj.read()
            print(f"Clip sample rate: {tree.get('m_SampleRate')}, length: {tree.get('m_MuscleClip', {}).get('m_StopTime')}")

