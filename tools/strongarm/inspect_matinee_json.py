import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import UnityPy
from pathlib import Path

for name, path in [
    ("PROWL OFFICIAL", Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")),
    ("PROWL REGISTERED", Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")),
    ("STRONGARM CURRENT", Path(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")),
]:
    print(f"\n================ {name} ================")
    env = UnityPy.load(str(path))
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            t = o.read_typetree()
            if "jSONData" in t:
                d = json.loads(t["jSONData"])
                tracks = d.get("TRACKS", {})
                print(f"MatineeData PID={o.path_id}: tracks={len(tracks)}")
                for tk, tv in sorted(tracks.items()):
                    if isinstance(tv, dict) and "econtainer" in tk:
                        for ek, ev in tv.items():
                            if isinstance(ev, dict) and "Mecanim" in ev.get("tt", ""):
                                print(f"  {tk}.{ek}: {json.dumps(ev, ensure_ascii=False)}")
                    elif isinstance(tv, dict) and "eid" in tv:
                        print(f"  track {tk}: enp={tv.get('enp')} en={tv.get('en')} eid={tv.get('eid')}")
        elif o.type.name == "AssetBundle":
            ab = o.read_typetree()
            print(f"AssetBundle m_Container len={len(ab.get('m_Container', []))}, m_PreloadTable len={len(ab.get('m_PreloadTable', []))}")
        elif o.type.name == "AnimatorOverrideController":
            aoc = o.read_typetree()
            if "fight" in aoc.get("m_Name", "").lower():
                ext_refs = getattr(o.assets_file, "externals", [])
                print(f"Fight AOC externals: {[(i+1, getattr(ex, 'name', str(ex))) for i, ex in enumerate(ext_refs)]}")
                for pair in aoc.get("m_Clips", []):
                    op = pair.get("m_OriginalClip", {})
                    ov = pair.get("m_OverrideClip", {})
                    if ov.get("m_PathID") in (5357267963671096457, 1518602965279940590) or op.get("m_PathID") in (3642901185112467297, -4048722777385356729):
                        print(f"  Victory override: orig={op} -> over={ov}")
