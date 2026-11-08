import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(g_bundle_path)

print("Asset names in container:")
for k, v in env.container.items():
    print(" ", k, "->", v.type.name)

print("\nAll AnimationClips in file and their path_id:")
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        print(f"  path_id={obj.path_id}: {name}")
