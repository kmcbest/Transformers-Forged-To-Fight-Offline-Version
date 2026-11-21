import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

RAMJET_BUNDLE = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
SKYWARP_BUNDLE = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"

def inspect_aocs(label, bp):
    print(f"\n================ {label} ================")
    e = UnityPy.load(str(bp))
    omap = {o.path_id: o for o in e.objects}
    # Print ALL AnimationClips
    clips = []
    for o in e.objects:
        if o.type.name == "AnimationClip":
            tt = o.read_typetree()
            clips.append((o.path_id, tt.get("m_Name", ""), tt.get("m_MuscleClip", {}).get("m_StopTime", 0)))
    print(f"AnimationClips ({len(clips)}):")
    for pid, n, dur in sorted(clips, key=lambda x: x[1]):
        if any(k in n.lower() for k in ("heavy", "prop", "jet", "trans", "idle", "special", "range")):
            print(f"  PID={pid}: '{n}' (dur={dur:.3f}s)")

    # Print AOC mappings for heavy/prop clips
    for o in e.objects:
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            aname = tt.get("m_Name", "")
            print(f"\nAOC '{aname}' (PID={o.path_id}, clips={len(tt.get('m_Clips', []))}):")
            for i, c in enumerate(tt.get("m_Clips", [])):
                opid = c["m_OriginalClip"]["m_PathID"]
                cpid = c["m_OverrideClip"]["m_PathID"]
                oname = omap[opid].read_typetree().get("m_Name") if opid in omap else f"ext({opid})"
                cname = omap[cpid].read_typetree().get("m_Name") if cpid in omap else f"ext({cpid})"
                if any(k in (oname + cname + aname).lower() for k in ("heavy", "jet", "prop", "trans")):
                    print(f"  [{i:2d}] orig='{oname}' ({opid}) -> ovr='{cname}' ({cpid})")

inspect_aocs("Skywarp", SKYWARP_BUNDLE)
inspect_aocs("Ramjet", RAMJET_BUNDLE)
