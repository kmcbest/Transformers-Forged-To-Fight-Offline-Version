import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path
import UnityPy

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

mv_env = UnityPy.load(str(ROOT_BL / "assets_redeco/moves.assetbundle"))
mv_map = {o.path_id: o for o in mv_env.objects}
pids = [7275783511033908245, -7662765974118130433, -4298719180494269477, 5165820106613088172, -8854555575616973088]
print("=== Donor Projectile MoveData in moves.assetbundle ===")
for pid in pids:
    if pid in mv_map:
        t = mv_map[pid].read()
        raw = t.m_Script if isinstance(t.m_Script, str) else t.m_Script.decode("utf-8", errors="replace")
        mv = json.loads(raw)["moves"]
        pns = [e.get("pn") for e in mv.get("events", []) if e.get("pn")]
        print(f"  PID={pid} name={t.m_Name} FXs={pns}")
    else:
        print(f"  MISSING PID={pid}")

# Also inspect Megatron's 3 projectile PrefabLists and Mixmaster/Sideswipe PrefabLists
for label, p in [
    ("MEGATRON", ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"),
    ("MIXMASTER", ROOT_GM / "extracted_apk/assets/assetpack/mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle"),
    ("SIDESWIPE", ROOT_GM / "extracted_apk/assets/assetpack/sideswipe_gs_deluxe2014_odr/sideswipe_gs_deluxe2014.assetbundle"),
]:
    env = UnityPy.load(str(p))
    objs = {o.path_id: o for o in env.objects}
    print(f"\n=== {label} PrefabLists ===")
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "PrefabList" in tt or "_prefabs" in tt:
                go = objs[tt["m_GameObject"]["m_PathID"]].read_typetree()
                plist = tt.get("PrefabList", tt.get("_prefabs", []))
                items = []
                for e in plist:
                    pr = e.get("Prefab", e)
                    if isinstance(pr, dict) and "m_PathID" in pr:
                        fid = pr.get("m_FileID", 0)
                        pid = pr.get("m_PathID", 0)
                        amt = e.get("Amount", "?")
                        nm = objs[pid].read_typetree().get("m_Name", "?") if fid == 0 and pid in objs else f"ext({fid},{pid})"
                        items.append(f"{nm}[x{amt}]")
                print(f"  GO={go['m_Name']} PID={o.path_id}: {items[:15]}")
