import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF\assets_redeco\blitzwing_gs.assetbundle")
for obj in env.objects:
    if obj.path_id == -4914847298671604126:
        tree = obj.read_typetree()
        print(f"=== {tree.get('m_Name')} ===")
        print("m_Controller:", tree.get("m_Controller"))
        for o in tree.get("m_Clips", []):
            orig = o.get("m_OriginalClip", {}).get("m_PathID")
            ovr = o.get("m_OverrideClip", {}).get("m_PathID")
            print(f"  orig={orig} -> ovr={ovr}")
