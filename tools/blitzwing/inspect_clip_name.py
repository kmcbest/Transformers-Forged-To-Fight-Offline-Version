import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

clip = obj_map.get(-643812257501667161)
if clip:
    d = clip.read()
    print("Clip name:", getattr(d, "m_Name", ""))
    print("Clip duration:", getattr(d, "m_StopTime", 0))
