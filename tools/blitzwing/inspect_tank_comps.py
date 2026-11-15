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
        print(f"\nGameObject {pid}: {tt.get('m_Name')}")
        for c in tt.get("m_Components", []):
            comp = obj_map.get(c.get("m_PathID"))
            print(f"  Component: {comp.type.name if comp else 'None'} ({c.get('m_PathID')})")
            if comp and "transform" in comp.type.name.lower():
                print("  Transform typetree:", comp.read_typetree())
