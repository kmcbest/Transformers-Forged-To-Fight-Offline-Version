import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

rj_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(rj_bundle))

for o in env.objects:
    if o.path_id == -6340484879223379266:
        tt = o.read_typetree()
        print(f"Ramjet Jet AOC (PID {o.path_id}): name={tt.get('m_Name')}")
        print(f"  BaseController: {tt.get('m_Controller')}")
        for c in tt.get("m_Clips", []):
            orig = c.get("m_OriginalClip", {})
            over = c.get("m_OverrideClip", {})
            print(f"  orig {orig.get('m_PathID')} -> over {over.get('m_PathID')}")
