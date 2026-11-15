import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

comp = obj_map.get(-4070916873066828308)
if comp:
    print(comp.type.name, comp.read_typetree())
