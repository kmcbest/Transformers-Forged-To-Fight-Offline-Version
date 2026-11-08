import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle"
env = UnityPy.load(g_bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        data = obj.read()
        name = getattr(data, 'name', '') or getattr(data, 'm_Name', '')
        if "01" in name or "vehicle" in name.lower():
            print(f"Mesh: {name}")
            skin = getattr(data, 'm_Skin', [])
            print(f"  Skin weights count: {len(skin)}")
            bone_usage = {}
            for s in skin:
                for b_idx, w in zip(s.boneIndex, s.weight):
                    if w > 0.01:
                        bone_usage[b_idx] = bone_usage.get(b_idx, 0) + 1
            print(f"  Bones used: {len(bone_usage)}")
            for b_idx, cnt in sorted(bone_usage.items(), key=lambda x: -x[1])[:10]:
                print(f"    Bone index {b_idx}: {cnt} vertices")
