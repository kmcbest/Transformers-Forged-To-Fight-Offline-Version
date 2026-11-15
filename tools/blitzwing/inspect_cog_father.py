import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

comp = obj_map.get(7256209656881810047)
if comp:
    go_pid = comp.read_typetree().get("m_GameObject", {}).get("m_PathID")
    go = obj_map.get(go_pid)
    print("Father GO:", go.read_typetree().get("m_Name"))
    print("Father Transform:", comp.read_typetree())
