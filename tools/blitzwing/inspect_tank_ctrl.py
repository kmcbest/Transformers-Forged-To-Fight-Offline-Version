import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))

for o in env.objects:
    if o.path_id == -3258403100930663047:
        tt = o.read_typetree()
        print("Type:", o.type.name)
        print("Name:", tt.get("m_Name"))
        print("Controller:", tt.get("m_Controller"))
        print("Clips:", len(tt.get("m_Clips", [])))
        for c in tt.get("m_Clips", []):
            orig = c.get("m_OriginalClip", {})
            over = c.get("m_OverrideClip", {})
            print(f"  orig {orig.get('m_PathID')} -> over {over.get('m_PathID')}")
