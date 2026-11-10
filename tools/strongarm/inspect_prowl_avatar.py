import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, "name", getattr(data, "m_Name", ""))
        if "prowl" in name.lower():
            print(f"Found GameObject: {name}")
            for comp in getattr(data, "m_Components", []):
                c = comp.read()
                c_type = type(c).__name__
                if c_type == "Animator":
                    print(f"  Component: {c_type}")
                    print("  applyRootMotion:", getattr(c, "m_ApplyRootMotion", None))
                    av = getattr(c, "m_Avatar", None)
                    print("  m_Avatar:", av)
                    if av and hasattr(av, "read"):
                        av_obj = av.read()
                        print("  Avatar name:", getattr(av_obj, "m_Name", None))
                        print("  Avatar isHuman:", hasattr(av_obj, "m_Human"))
    elif obj.type.name == "Avatar":
        data = obj.read()
        print(f"Found Avatar: {getattr(data, 'm_Name', '')}, isHuman: {hasattr(data, 'm_Human')}")
