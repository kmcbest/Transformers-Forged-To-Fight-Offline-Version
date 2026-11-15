import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

for pid in (-5385736693872477217, 6479682388170250398):
    go = obj_map.get(pid)
    if go:
        tt = go.read_typetree()
        print(f"\nGameObject {pid}: {tt.get('m_Name')}, IsActive={tt.get('m_IsActive')}")
        for c in tt.get("m_Components", []):
            comp = obj_map.get(c.get("m_PathID"))
            if comp and comp.type.name == "Transform":
                t_tt = comp.read_typetree()
                p_pid = t_tt.get("m_Father", {}).get("m_PathID")
                p_comp = obj_map.get(p_pid)
                p_go_pid = p_comp.read_typetree().get("m_GameObject", {}).get("m_PathID") if p_comp else 0
                p_go = obj_map.get(p_go_pid)
                print(f"  Parent: {p_go.read_typetree().get('m_Name') if p_go else 'None'}")
                print(f"  LocalPos: {t_tt.get('m_LocalPosition')}")
                print(f"  LocalRot: {t_tt.get('m_LocalRotation')}")
                print(f"  LocalScale: {t_tt.get('m_LocalScale')}")
