import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read_typetree()
        if data.get("m_Name") == "Brute_Normal_CombatIdle":
            print("Found Brute_Normal_CombatIdle!")
            print("m_SampleRate:", data.get("m_SampleRate"))
            curves = data.get("m_EulerCurves", [])
            print("m_EulerCurves count:", len(curves))
            generic_bindings = data.get("m_ClipBindingConstant", {}).get("genericBindings", [])
            print("genericBindings count:", len(generic_bindings))
            paths = set()
            for b in generic_bindings[:15]:
                print(f"  Binding: path_hash={b.get('path')}, attribute={b.get('attribute')}, typeID={b.get('typeID')}")
