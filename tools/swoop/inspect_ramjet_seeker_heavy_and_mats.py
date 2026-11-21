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
STARSCREAM_BUNDLE = TFTF / "extracted_apk/assets/assetpack/starscream_gs_odr/starscream_gs.assetbundle"
THUNDER_BUNDLE = TFTF / "extracted_apk/assets/assetpack/thundercracker_gs_leader2015_odr/thundercracker_gs_leader2015.assetbundle"
MOVES_BUNDLE = ROOT / "assets_redeco/moves.assetbundle"

print("=== 1. Check Seeker Heavy Moves in moves.assetbundle ===")
env_mv = UnityPy.load(str(MOVES_BUNDLE))
for o in env_mv.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        name = tt.get("m_Name", "")
        if "move_heavy_" in name and any(k in name for k in ("ramjet", "starscream", "skywarp", "thundercracker", "seeker", "swoop", "grimlock", "thrust")):
            script = tt.get("m_Script", "")
            if isinstance(script, bytes):
                script = script.decode("utf-8", errors="replace")
            print(f"\n--- {name} (PID={o.path_id}) ---")
            try:
                data = json.loads(script)
                print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])
            except Exception as e:
                print(f"raw: {script[:800]}")

print("\n=== 2. Check Seeker Bundles & Heavy Clips ===")
for label, bp in [("Ramjet", RAMJET_BUNDLE), ("Skywarp", SKYWARP_BUNDLE), ("Starscream", STARSCREAM_BUNDLE), ("Thundercracker", THUNDER_BUNDLE)]:
    print(f"\n--- {label}: exists={bp.is_file()} ---")
    if not bp.is_file():
        continue
    e = UnityPy.load(str(bp))
    omap = {o.path_id: o for o in e.objects}
    for o in e.objects:
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            print(f"  AOC '{tt.get('m_Name')}' PID={o.path_id}")
            for i, c in enumerate(tt.get("m_Clips", [])):
                opid = c["m_OriginalClip"]["m_PathID"]
                cpid = c["m_OverrideClip"]["m_PathID"]
                oname = omap[opid].read_typetree().get("m_Name") if opid in omap else str(opid)
                cname = omap[cpid].read_typetree().get("m_Name") if cpid in omap else str(cpid)
                if "heavy" in oname.lower() or "heavy" in cname.lower() or "missile" in cname.lower():
                    print(f"    [{i}] orig={oname} -> ovr={cname} (PID={cpid})")
        elif o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_moves" in tt:
                print(f"  MoveSet '{tt.get('m_Name')}' PID={o.path_id}")
                for i, m in enumerate(tt.get("_moves", [])):
                    if "heavy" in m.get("_animStateName", "").lower() or "heavy" in m.get("_name", "").lower():
                        print(f"    [{i}] {m.get('_animStateName')} -> {m.get('_name')} ({m.get('_asset')})")

print("\n=== 3. Check Ramjet Materials & SMR Submesh Mapping in detail ===")
er = UnityPy.load(str(RAMJET_BUNDLE))
rmap = {o.path_id: o for o in er.objects}
for mpid in [1469909421462177924, 3520121911555544087, -6074135333607175177, 3595971348910711679]:
    mtt = rmap[mpid].read_typetree()
    print(f"\nMaterial PID={mpid} ('{mtt.get('m_Name')}'):")
    print("  m_Floats:", mtt["m_SavedProperties"]["m_Floats"])
    print("  m_Colors:", mtt["m_SavedProperties"]["m_Colors"])
    print("  m_TexEnvs:", [(k, {"pid": v["m_Texture"]["m_PathID"], "scale": v["m_Scale"], "offset": v["m_Offset"]}) for k, v in mtt["m_SavedProperties"]["m_TexEnvs"]])
