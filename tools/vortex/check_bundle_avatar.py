import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Avatar":
        data = obj.read()
        print(f"Found Avatar: {data.m_Name}")
    elif obj.type.name == "Animator":
        data = obj.read()
        print(f"Found Animator: m_Avatar={getattr(data, 'm_Avatar', None)}")
