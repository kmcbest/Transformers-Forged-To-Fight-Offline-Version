import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import zlib
import UnityPy
from pathlib import Path

TFTF = Path(r"E:\Agent\TFTF")
RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"
PROC = TFTF / "extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle"

er = UnityPy.load(str(RAMJET))
rmap = {o.path_id: o for o in er.objects}
es = UnityPy.load(str(SKYWARP))
smap = {o.path_id: o for o in es.objects}
ep = UnityPy.load(str(PROC))
pmap = {o.path_id: o for o in ep.objects}

def build_crc_map(omap, root_go_name):
    crc_map = {}
    root_go = next(o.read_typetree() for o in omap.values() if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == root_go_name)
    root_tr_pid = next(c["component"]["m_PathID"] for c in root_go["m_Component"] if omap[c["component"]["m_PathID"]].type.name == "Transform")
    def walk(tr_pid, prefix):
        tr = omap[tr_pid].read_typetree()
        gn = omap[tr["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"]
        p = f"{prefix}/{gn}" if prefix else gn
        crc_map[zlib.crc32(p.encode("utf-8")) & 0xFFFFFFFF] = p
        for ch in tr["m_Children"]:
            walk(ch["m_PathID"], p)
    for ch in omap[root_tr_pid].read_typetree()["m_Children"]:
        walk(ch["m_PathID"], "")
    # Also root of transformed child: find GO named 'transformed'
    for o in omap.values():
        if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == "transformed":
            t_go = o.read_typetree()
            t_tr_pid = next(c["component"]["m_PathID"] for c in t_go["m_Component"] if omap[c["component"]["m_PathID"]].type.name == "Transform")
            def walk_t(tr_pid, prefix):
                tr = omap[tr_pid].read_typetree()
                gn = omap[tr["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"]
                p = f"{prefix}/{gn}" if prefix else gn
                crc_map[zlib.crc32(p.encode("utf-8")) & 0xFFFFFFFF] = f"[transformed]/{p}"
                for ch in tr["m_Children"]:
                    walk_t(ch["m_PathID"], p)
            for ch in omap[t_tr_pid].read_typetree()["m_Children"]:
                walk_t(ch["m_PathID"], "")
            break
    return crc_map

r_crc = build_crc_map(rmap, "Ramjet_GS_Deluxe2008")
s_crc = build_crc_map(smap, "Skywarp_GS_Leader2015")
merged_crc = {**s_crc, **r_crc}

for label, pid in [
    ("StarScream_Normal_attackHeavy", 7645321843667068633),
    ("StarScream_Normal_attackHeavy_transformed", -7989888022101248653),
    ("Ramjet_Normal_attackHeavy", -8287216037977883126),
    ("Ramjet_Normal_attackHeavy_transformed", 2235498278053343569),
    ("Swoop_Vehicle_WingFlap_transformed", None),
]:
    if pid is None:
        continue
    tt = pmap[pid].read_typetree()
    gen = tt["m_ClipBindingConstant"]["genericBindings"]
    print(f"\n=== {label} (dur={tt['m_MuscleClip']['m_StopTime']:.3f}s, total bindings={len(gen)}) ===")
    non_muscle = [b for b in gen if b["path"] != 0]
    print(f"  path==0 bindings: {len(gen) - len(non_muscle)}, path!=0 bindings: {len(non_muscle)}")
    for b in non_muscle:
        p = merged_crc.get(b["path"], f"hash({b['path']})")
        print(f"    path='{p}', attr={b['attribute']}, typeID={b['typeID']}, customType={b['customType']}")

print("\n=== Check PrefabLib / projectile_ramjet_* mesh usage ===")
for go_name in ["projectile_ramjet_big_missile", "projectile_ramjet_missile", "projectile_ramjet_bullet", "Ramjet_GS_Deluxe2008"]:
    for o in er.objects:
        if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == go_name:
            tt = o.read_typetree()
            print(f"GO '{go_name}' PID={o.path_id}: comps={[rmap[c['component']['m_PathID']].type.name for c in tt['m_Component']]}")
