import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))

JET_AOC_PID = -4914847298671604126
for o in env.objects:
    if o.path_id == JET_AOC_PID:
        tt = o.read_typetree()
        print("AOC:", tt.get("m_Name"))
        print("  BaseController:", tt.get("m_Controller"))
        clips = tt.get("m_Clips", [])
        print(f"  Clips count: {len(clips)}")
        for c in clips:
            orig = c.get("m_OriginalClip", {})
            over = c.get("m_OverrideClip", {})
            print(f"    orig PathID={orig.get('m_PathID')} -> over PathID={over.get('m_PathID')}")
