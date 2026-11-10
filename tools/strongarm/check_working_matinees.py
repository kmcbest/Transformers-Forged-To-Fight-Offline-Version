import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import UnityPy
from pathlib import Path

for name, path in [
    ("ELITA ONE WORKING", Path(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")),
    ("ONSLAUGHT WORKING", Path(r"E:\Agent\TFTF-blender\assets_redeco\onslaught_gs.assetbundle")),
]:
    print(f"\n=== {name} ===")
    env = UnityPy.load(str(path))
    for o in env.objects:
        if o.type.name == "AssetBundle":
            ab = o.read_typetree()
            print(f"m_Container len={len(ab.get('m_Container', []))}, keys={[x[0] for x in ab.get('m_Container', [])]}")
        elif o.type.name == "MonoBehaviour":
            t = o.read_typetree()
            if "jSONData" in t:
                d = json.loads(t["jSONData"])
                tracks = d.get("TRACKS", {})
                mec = [tk for tk, tv in tracks.items() if isinstance(tv, dict) and "Mecanim" in str(tv)]
                eids = [tv.get("eid") for tk, tv in tracks.items() if isinstance(tv, dict) and "eid" in tv]
                print(f"MatineeData tracks={len(tracks)}, MecanimEvents={mec}, eids_sample={eids[:5]}")
            elif "actorInfoList" in t:
                print(f"TFormMatineeStage: actors={t.get('actorInfoList')}, clips={t.get('_matineeAnimationClipList')}")
        elif o.type.name == "AnimatorOverrideController":
            aoc = o.read_typetree()
            print(f"AOC: {aoc.get('m_Name')}, clips={len(aoc.get('m_Clips', []))}")
