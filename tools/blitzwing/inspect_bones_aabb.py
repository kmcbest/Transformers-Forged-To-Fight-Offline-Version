import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

mesh = obj_map.get(8396146535644667895)
if mesh:
    tt = mesh.read_typetree()
    print("BonesAABB:", tt.get("m_BonesAABB"))
