import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF\assets_redeco\blitzwing_gs.assetbundle")
JET_AOC_PID = -1671981242398506087
for obj in env.objects:
    if obj.path_id == JET_AOC_PID:
        tree = obj.read_typetree()
        print(f"=== Jet Prop AOC: {tree.get('m_Name')} ===")
        for o in tree.get("m_Clips", []):
            orig = o.get("m_OriginalClip", {}).get("m_PathID")
            ovr = o.get("m_OverrideClip", {}).get("m_PathID")
            print(f"  orig={orig} -> ovr={ovr}")
        break
