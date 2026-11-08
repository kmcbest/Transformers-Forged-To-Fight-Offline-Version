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

# Load TOS of cha_grindor_cin_rotf_01Avatar
tos_01 = {}
for obj in env.objects:
    if obj.type.name == "Avatar":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_grindor_cin_rotf_01Avatar":
            for h, path in tree.get("m_TOS", []):
                tos_01[int(h)] = path

print(f"cha_grindor_cin_rotf_01Avatar has {len(tos_01)} bones in TOS:")
for h, path in sorted(tos_01.items(), key=lambda x: x[1]):
    print(f"  {h:10d} -> {path}")

# Check clip paths
clip_paths = set()
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "frontend_Grindor_levelup_vehicle_idle_transformed":
            for b in tree.get("m_ClipBindingConstant", {}).get("genericBindings", []):
                clip_paths.add(b.get("path"))

print(f"\nMatching against frontend_Grindor_levelup_vehicle_idle_transformed (48 bones):")
matches = 0
for h in clip_paths:
    if h in tos_01:
        matches += 1
        print(f"  [✓] {tos_01[h]}")
    else:
        print(f"  [?] Unknown hash {h}")

print(f"Total matched: {matches} / {len(clip_paths)}")

