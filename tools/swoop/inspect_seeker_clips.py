import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

TFTF = Path(r"E:\Agent\TFTF")
RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"

# Find all character_anim bundles
anim_bundles = list((TFTF / "extracted_apk/assets").rglob("*character_anim*.assetbundle"))
print("Found anim bundles:", [str(p) for p in anim_bundles])

clip_lookup = {}
for bp in anim_bundles:
    e = UnityPy.load(str(bp))
    for o in e.objects:
        if o.type.name == "AnimationClip":
            tt = o.read_typetree()
            clip_lookup[o.path_id] = (bp.name, tt.get("m_Name", ""), tt.get("m_MuscleClip", {}).get("m_StopTime", 0))

print("\n=== Target CLIP PIDs from Ramjet / Skywarp ===")
target_pids = [
    -643812257501667161,
    -8287216037977883126,
    -4177997624914663523,
    -1877059238783929753,
    8156662034948264509,
    5620803938405291589,
    3658090888164254241,
    -8823098701810809179,
    -121750790583225863,
]
for pid in target_pids:
    print(f"  {pid}: {clip_lookup.get(pid, 'NOT FOUND')}")

print("\n=== All Seeker/Starscream/Skywarp/Jet Heavy Clips in character_anim* ===")
for pid, (bname, cname, dur) in sorted(clip_lookup.items(), key=lambda x: x[1][1]):
    if "heavy" in cname.lower() and any(k in cname.lower() for k in ("jet", "star", "sky", "seek", "ram", "thund", "prop")):
        print(f"  [{bname}] PID={pid}: '{cname}' (dur={dur:.3f}s)")

print("\n=== Skywarp Fight AOC (PID=5661215193959676599) resolved ===")
es = UnityPy.load(str(SKYWARP))
for o in es.objects:
    if o.path_id == 5661215193959676599:
        tt = o.read_typetree()
        for i, c in enumerate(tt.get("m_Clips", [])):
            opid = c["m_OriginalClip"]["m_PathID"]
            cpid = c["m_OverrideClip"]["m_PathID"]
            oname = clip_lookup.get(opid, ("", str(opid), 0))[1]
            cname = clip_lookup.get(cpid, ("", str(cpid), 0))[1]
            if "heavy" in (oname + cname).lower():
                print(f"  [{i:2d}] orig='{oname}' ({opid}) -> ovr='{cname}' ({cpid})")
