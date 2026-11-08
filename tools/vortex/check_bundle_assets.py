import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle"
env = UnityPy.load(bundle_path)

print("=== Assets in grindor_anims_registered.assetbundle ===")
for obj in env.objects:
    if obj.type.name in ["GameObject", "Avatar", "AnimationClip", "SkinnedMeshRenderer"]:
        data = obj.read()
        name = getattr(data, 'm_Name', getattr(data, 'name', 'unnamed'))
        print(f"[{obj.type.name}] {name}")
