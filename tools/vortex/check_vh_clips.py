import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF-blender\toolchain\grindor_anims_registered.assetbundle"
env = UnityPy.load(g_bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        if "vehicle" in name.lower() or "levelup" in name.lower():
            print(f"Clip: {name}")
            bindings = getattr(data, 'm_ClipBindingConstant', None)
            if bindings:
                print(f"  genericBindings: {len(getattr(bindings, 'genericBindings', []))}")
                for b in getattr(bindings, 'genericBindings', [])[:5]:
                    print(f"    path={getattr(b, 'path', 'N/A')}, typeID={getattr(b, 'typeID', 'N/A')}")
