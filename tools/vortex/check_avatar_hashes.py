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

# Check avatar m_BoneNameHash vs clip binding paths
avatar_hashes = {}
for obj in env.objects:
    if obj.type.name == "Avatar":
        tree = obj.read_typetree()
        print(f"Avatar: {tree.get('m_Name')}")
        tos = tree.get("m_TOS", {})
        for h, name in tos.items():
            avatar_hashes[int(h)] = name
        print(f"  TOS entries: {len(tos)}")

clip_paths = set()
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "frontend_Grindor_levelup_vehicle_idle_transformed":
            for b in tree.get("m_ClipBindingConstant", {}).get("genericBindings", []):
                clip_paths.add(b.get("path"))

print(f"Clip unique paths: {len(clip_paths)}")
matches = []
for p in clip_paths:
    if p in avatar_hashes:
        matches.append((p, avatar_hashes[p]))
    else:
        print(f"Unmatched path: {p}")

print(f"\nMatched in Avatar: {len(matches)} / {len(clip_paths)}")
for p, name in sorted(matches, key=lambda x: x[1]):
    print(f"  Hash {p:10d} -> {name}")

