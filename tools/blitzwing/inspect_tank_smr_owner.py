import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

for pid in (2138194849323017337, 4626197738286450028):
    smr = obj_map.get(pid)
    if smr:
        tt = smr.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        go = obj_map.get(go_pid)
        print(f"Tank SMR PID {pid}: GameObject {go_pid} -> {go.read_typetree().get('m_Name') if go else 'None'}")
