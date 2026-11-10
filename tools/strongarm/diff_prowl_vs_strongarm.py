import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import UnityPy
from pathlib import Path

# 1. Check Elita One PlayMecanimAnimationEvent tracks
env_e = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")
for o in env_e.objects:
    if o.type.name == "MonoBehaviour":
        t = o.read_typetree()
        if "jSONData" in t:
            d = json.loads(t["jSONData"])
            for tk, tv in sorted(d.get("TRACKS", {}).items()):
                if isinstance(tv, dict) and ("track_5" in tk or "track_11" in tk or "Mecanim" in str(tv)):
                    print(f"ELITA {tk}: {tv}")

# 2. Check diff of object counts/types between PROWL OFFICIAL vs PROWL REGISTERED vs STRONGARM CURRENT
p_off = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
p_reg = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
p_sa = Path(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")

for lbl, p in [("PROWL OFFICIAL", p_off), ("PROWL REGISTERED", p_reg), ("STRONGARM CURRENT", p_sa)]:
    env = UnityPy.load(str(p))
    objs = {o.path_id: o for o in env.objects}
    bf = list(env.files.values())[0]
    sf = next(f for f in bf.files.values() if hasattr(f, "externals"))
    anims = [o.read_typetree().get("m_Name") for o in env.objects if o.type.name == "AnimationClip"]
    print(f"\n[{lbl}] total objs={len(objs)}, externals={[(i+1, getattr(e, 'path', str(e))) for i, e in enumerate(sf.externals)]}")
    print(f"  AnimationClips ({len(anims)}): {anims}")
    # Inspect AOCs in each
    for o in env.objects:
        if o.type.name == "AnimatorOverrideController":
            aoc = o.read_typetree()
            print(f"  AOC '{aoc.get('m_Name')}' PID={o.path_id} m_Controller={aoc.get('m_Controller')} clips={len(aoc.get('m_Clips', []))}")
            # Check if ANY override points to missing m_FileID or unexpected PID
            for c in aoc.get("m_Clips", []):
                ov = c.get("m_OverrideClip", {})
                if ov.get("m_FileID") == 0 and ov.get("m_PathID") != 0 and ov.get("m_PathID") not in objs:
                    print(f"    [BROKEN REF!] orig={c.get('m_OriginalClip')} -> over={ov}")
