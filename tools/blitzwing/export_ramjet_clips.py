import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, json

rj_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(rj_bundle))

for o in env.objects:
    if o.path_id == -6340484879223379266:
        tt = o.read_typetree()
        print("Ramjet Jet AOC m_Clips:")
        clips = tt.get("m_Clips", [])
        print(f"Total clips: {len(clips)}")
        # Print Python literal
        print("RAMJET_JET_CLIPS = [")
        for c in clips:
            print(f"    {json.dumps(c)},")
        print("]")
