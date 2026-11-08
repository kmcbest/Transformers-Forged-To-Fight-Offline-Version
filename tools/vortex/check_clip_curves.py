import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(g_bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        if name in ["Brute_Normal_CombatIdle", "Grindor_Normal_attackSpecial_02"]:
            print(f"--- Clip: {name} ---")
            print(f"  m_Legacy: {getattr(data, 'm_Legacy', 'N/A')}")
            print(f"  m_HumanMotion: {getattr(data, 'm_HumanMotion', 'N/A')}")
            # check curves or bindings
            bindings = getattr(data, 'm_ClipBindingConstant', None)
            if bindings:
                generic_bindings = getattr(bindings, 'genericBindings', [])
                print(f"  genericBindings count: {len(generic_bindings)}")
                for b in generic_bindings[:10]:
                    print(f"    path={getattr(b, 'path', 'N/A')}, attribute={getattr(b, 'attribute', 'N/A')}, typeID={getattr(b, 'typeID', 'N/A')}, classID={getattr(b, 'classID', 'N/A')}")
