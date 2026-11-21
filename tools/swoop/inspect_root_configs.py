import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"
GRIM = TFTF / "extracted_apk/assets/assetpack/grimlock_gs_mp08_odr/grimlock_gs_mp08.assetbundle"

for label, bp, rname in [
    ("Ramjet", RAMJET, "Ramjet_GS_Deluxe2008"),
    ("Skywarp", SKYWARP, "Skywarp_GS_Leader2015"),
    ("Grimlock", GRIM, "Grimlock_GS_MP08"),
]:
    e = UnityPy.load(str(bp))
    omap = {o.path_id: o for o in e.objects}
    print(f"\n=== {label} Root GO '{rname}' Components & Scale MonoBehaviours ===")
    rgo = next(o.read_typetree() for o in e.objects if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == rname)
    for c in rgo["m_Component"]:
        co = omap[c["component"]["m_PathID"]]
        tt = co.read_typetree()
        if co.type.name == "MonoBehaviour":
            keys = [k for k in tt.keys() if k not in ("m_GameObject", "m_Enabled", "m_Script", "m_Name")]
            print(f"  MB PID={co.path_id}: keys={keys}")
            for k in keys:
                if k in ("_moves", "PrefabList", "_props"):
                    continue
                val = tt[k]
                if isinstance(val, (int, float, bool, str)) or (isinstance(val, dict) and len(val) < 6):
                    print(f"    {k} = {val}")
        elif co.type.name == "Animator":
            ctrl = tt.get("m_Controller", {})
            c_name = omap[ctrl["m_PathID"]].read_typetree().get("m_Name") if ctrl.get("m_PathID") in omap else str(ctrl)
            av = tt.get("m_Avatar", {})
            av_name = omap[av["m_PathID"]].read_typetree().get("m_Name") if av.get("m_PathID") in omap else str(av)
            print(f"  Animator PID={co.path_id}: ctrl={c_name} ({ctrl}), avatar={av_name} ({av}), applyRootMotion={tt.get('m_ApplyRootMotion')}")
