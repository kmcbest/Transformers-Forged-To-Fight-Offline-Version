import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(g_bundle_path)

for obj in env.objects:
    if obj.type.name == "Avatar":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        print(f"Avatar: {name}, isHuman: {getattr(data, 'm_Avatar', None)}")
    elif obj.type.name == "GameObject":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        if "grindor" in name.lower():
            for comp in getattr(data, 'm_Components', []):
                try:
                    cobj = comp.read()
                    if cobj.type.name == "Animator":
                        print(f"GameObject '{name}' has Animator, avatar: {getattr(cobj, 'm_Avatar', None)}")
                except:
                    pass
