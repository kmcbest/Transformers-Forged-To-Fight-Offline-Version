import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

RAMJET_BUNDLE = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
SKYWARP_BUNDLE = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"
MOVES_BUNDLE = ROOT / "assets_redeco/moves.assetbundle"

print("=== 1. Full Events of move_heavy_starscream_shoot, move_heavy_ramjet_donut, move_heavy_grimlock, move_heavy_swoop ===")
env_mv = UnityPy.load(str(MOVES_BUNDLE))
for o in env_mv.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        name = tt.get("m_Name", "")
        if name in ("move_heavy_starscream_shoot", "move_heavy_ramjet_donut", "move_heavy_grimlock", "move_heavy_swoop"):
            script = tt.get("m_Script", "")
            if isinstance(script, bytes):
                script = script.decode("utf-8", errors="replace")
            data = json.loads(script)
            print(f"\n=== {name} ===")
            for ev in data["moves"]["events"]:
                print(json.dumps(ev, ensure_ascii=False))

print("\n=== 2. Ramjet Clip -8287216037977883126 & Skywarp Heavy Clip ===")
for label, bp in [("Ramjet", RAMJET_BUNDLE), ("Skywarp", SKYWARP_BUNDLE)]:
    e = UnityPy.load(str(bp))
    omap = {o.path_id: o for o in e.objects}
    for o in e.objects:
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            if "fight" in tt.get("m_Name", "").lower():
                for i, c in enumerate(tt.get("m_Clips", [])):
                    opid = c["m_OriginalClip"]["m_PathID"]
                    cpid = c["m_OverrideClip"]["m_PathID"]
                    oname = omap[opid].read_typetree().get("m_Name") if opid in omap else str(opid)
                    cname = omap[cpid].read_typetree().get("m_Name") if cpid in omap else str(cpid)
                    if "heavy" in oname.lower() or "heavy" in cname.lower():
                        ctt = omap[cpid].read_typetree()
                        mus = ctt.get("m_MuscleClip", {})
                        stop_t = mus.get("m_StopTime")
                        print(f"{label} Fight[{i}] orig={oname} -> clip='{cname}' (PID={cpid}), duration={stop_t}")
                        # Check root motion or Hip curves if present
                        for bname in ("m_ClipBindingConstant",):
                            if bname in ctt:
                                gen_curves = ctt[bname].get("genericBindings", [])
                                print(f"  genericBindings count={len(gen_curves)}")
                                for gb in gen_curves[:15]:
                                    print(f"    path={gb.get('path')}, attr={gb.get('attribute')}, classID={gb.get('classID')}")

print("\n=== 3. Check if any Ramjet AnimationClip touches wpns / rocket / chest / missile ===")
er = UnityPy.load(str(RAMJET_BUNDLE))
rmap = {o.path_id: o for o in er.objects}
# Check PPtrs or path hashes? Let's print all GOs and Transforms for wpns
for o in er.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        n = tt.get("m_Name", "")
        if "wpn" in n.lower() or "ramjet" in n.lower():
            print(f"  GO PID={o.path_id}: '{n}', active={tt.get('m_IsActive')}")
