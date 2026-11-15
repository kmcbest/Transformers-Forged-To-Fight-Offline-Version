import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

for pid in (-6221277661502632596, -6299151529957601360):
    go = obj_map.get(pid)
    if go:
        print(f"Jet GO {pid}:", go.read_typetree())
