import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bp = r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle"
env = UnityPy.load(bp)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', getattr(d, 'm_Name', ''))
        if name == "frontend_Prowl_levelup_vehicle_idle_transformed":
            print(f"Found clip: {name}")
            b = getattr(d, "m_ClipBindingConstant", None)
            if b:
                gb = getattr(b, "genericBindings", None)
                print(f"genericBindings count: {len(gb) if gb else 0}")
                for item in (gb or [])[:20]:
                    print("  path:", getattr(item, "path", None), "attr:", getattr(item, "attribute", None))
