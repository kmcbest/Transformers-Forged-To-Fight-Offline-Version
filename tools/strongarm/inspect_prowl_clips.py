import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle"
env = UnityPy.load(bundle_path)

print(f"Total objects in {bundle_path}: {len(env.objects)}")
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, "name", None) or getattr(data, "m_Name", "Unknown")
        print(f"AnimationClip: {name}")
