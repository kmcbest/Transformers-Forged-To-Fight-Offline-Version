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

# Check clips
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        c_name = tree.get("m_Name", "")
        if "vehicle" in c_name.lower() or "levelup" in c_name.lower():
            print(f"--- Clip: {c_name} ---")
            bindings = tree.get("m_ClipBindingConstant", {}).get("genericBindings", [])
            print(f"Generic bindings count: {len(bindings)}")
            for b in bindings[:10]:
                print(f"  path={b.get('path')}, attribute={b.get('attribute')}, typeID={b.get('typeID')}")
            # Also check float/sample curves
            euler_crvs = tree.get("m_EulerCurves", [])
            print(f"Euler curves: {len(euler_crvs)}")
            rot_crvs = tree.get("m_RotationCurves", [])
            print(f"Rot curves: {len(rot_crvs)}")
            scale_crvs = tree.get("m_ScaleCurves", [])
            print(f"Scale curves: {len(scale_crvs)}")
            pos_crvs = tree.get("m_PositionCurves", [])
            print(f"Position curves: {len(pos_crvs)}")

