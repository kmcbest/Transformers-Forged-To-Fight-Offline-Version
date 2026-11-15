import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

clip = obj_map.get(2235498278053343569)
if clip:
    tt = clip.read_typetree()
    print("Clip Name:", tt.get("m_Name"))
    print("Clip StopTime:", tt.get("m_StopTime"))
    print("Clip SampleRate:", tt.get("m_SampleRate"))
    for curve in tt.get("m_ClipBindingConstant", {}).get("genericBindings", [])[:10]:
        print("Binding:", curve)
