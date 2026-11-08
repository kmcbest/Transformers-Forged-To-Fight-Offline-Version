import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# Check grindor_cin_rotf.assetbundle or grindor_anims_registered.assetbundle
p_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle")
if not p_bundle.exists():
    p_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")

env = UnityPy.load(str(p_bundle))

print("=== Checking Grindor 01 Mesh Bone Weights ===")
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01":
            print("Found cha_grindor_cin_rotf_01!")
            skin = tree.get("m_Skin", [])
            print(f"Skin count: {len(skin)}")
            # Let's count vertices per bone
            bone_usage = {}
            for item in skin:
                b0 = item.get("m_BoneIndex", [0])[0]
                w0 = item.get("m_Weight", [0])[0]
                bone_usage[b0] = bone_usage.get(b0, 0) + 1
            print(f"Bones used: {len(bone_usage)}, summary: {bone_usage}")

print("\n=== Checking Animation Clips for Rotor Curves ===")
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        c = obj.read()
        tree = obj.read_typetree()
        # Check if clip has curves for RotorMain or Rotor
        rotor_curves = []
        for crv in tree.get("m_RotationCurves", []):
            path = crv.get("path", "")
            if "rotor" in path.lower() or "prop" in path.lower():
                rotor_curves.append(path)
        for crv in tree.get("m_EulerCurves", []):
            path = crv.get("path", "")
            if "rotor" in path.lower() or "prop" in path.lower():
                rotor_curves.append(path)
        if rotor_curves:
            print(f"Clip '{c.name}': {len(rotor_curves)} rotor curves, e.g. {rotor_curves[:3]}")

