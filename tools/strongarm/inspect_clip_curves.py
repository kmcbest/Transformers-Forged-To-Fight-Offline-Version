import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, "name", None) or getattr(data, "m_Name", "Unknown")
        if name in ["tactical_normal_idle", "tactical_normal_attacklight_02_jab_R"]:
            print(f"--- AnimationClip: {name} ---")
            raw = data.get_raw_data() if hasattr(data, 'get_raw_data') else None
            # inspect clip properties
            print("m_Legacy:", getattr(data, "m_Legacy", None))
            binding = getattr(data, "m_ClipBindingConstant", None)
            if binding:
                gb = getattr(binding, "genericBindings", None)
                if gb:
                    print(f"genericBindings count: {len(gb)}")
                    for b in gb[:10]:
                        print("  path:", getattr(b, "path", None), "attribute:", getattr(b, "attribute", None))
            # print tos (type of structure)
            tos = getattr(data, "m_MuscleClip", None)
            print("m_MuscleClip:", tos is not None)
