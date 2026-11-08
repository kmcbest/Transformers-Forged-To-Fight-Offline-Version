import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(g_bundle_path)

for obj in env.objects:
    if obj.type.name in ["SkinnedMeshRenderer", "MeshRenderer"]:
        data = obj.read()
        go_name = ""
        try:
            go = data.m_GameObject.read()
            go_name = getattr(go, 'm_Name', '')
        except:
            pass
        print(f"{obj.type.name}: name={getattr(data, 'm_Name', '')}, go={go_name}")
