import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import zlib
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
PROC = TFTF / "extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle"
MESH_BUNDLE = ROOT / "toolchain/unity_build_project/AssetBundles/swoop_mesh.assetbundle"

ep = UnityPy.load(str(PROC))
pmap = {o.path_id: o for o in ep.objects}
er = UnityPy.load(str(RAMJET))
rmap = {o.path_id: o for o in er.objects}
em = UnityPy.load(str(MESH_BUNDLE))

# Print Ramjet wpns GO parent hierarchy & components
print("=== 1. Ramjet wpns GO Hierarchy (Main Prefab 1529847556182042256) ===")
def get_go_of_tr(tr_pid):
    tr = rmap[tr_pid].read_typetree()
    return rmap[tr["m_GameObject"]["m_PathID"]].read_typetree()

def walk_wpns(tr_pid, path=""):
    tr = rmap[tr_pid].read_typetree()
    go = rmap[tr["m_GameObject"]["m_PathID"]].read_typetree()
    gname = go["m_Name"]
    cur = f"{path}/{gname}" if path else gname
    if "wpn" in gname.lower() or "transformed" in gname.lower() or gname.startswith("cha_"):
        comps = [rmap[c["component"]["m_PathID"]].type.name for c in go["m_Component"]]
        smr_en = None
        for c in go["m_Component"]:
            co = rmap[c["component"]["m_PathID"]]
            if co.type.name == "SkinnedMeshRenderer":
                smr_en = co.read_typetree().get("m_Enabled")
        print(f"  {cur} | GO_PID={tr['m_GameObject']['m_PathID']} active={go['m_IsActive']} smr_en={smr_en} comps={comps}")
    for ch in tr["m_Children"]:
        walk_wpns(ch["m_PathID"], cur)

root_go = rmap[1529847556182042256].read_typetree()
root_tr_pid = next(c["component"]["m_PathID"] for c in root_go["m_Component"] if rmap[c["component"]["m_PathID"]].type.name == "Transform")
walk_wpns(root_tr_pid)

# Check root transform of Swoop_Vehicle_WingFlap_transformed & COG positions in Ramjet vs Starscream
print("\n=== 2. Swoop_Vehicle_WingFlap_transformed Curve Names & Positions ===")
# Build full relative path hashes under transformed GO in Ramjet AND under swoop_vh
t_go = next(o.read_typetree() for o in er.objects if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == "transformed")
t_tr_pid = next(c["component"]["m_PathID"] for c in t_go["m_Component"] if rmap[c["component"]["m_PathID"]].type.name == "Transform")
t_crc = {}
def walk_t(tr_pid, prefix=""):
    tr = rmap[tr_pid].read_typetree()
    gn = rmap[tr["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"]
    p = f"{prefix}/{gn}" if prefix else gn
    t_crc[zlib.crc32(p.encode("utf-8")) & 0xFFFFFFFF] = (p, tr["m_LocalPosition"])
    t_crc[zlib.crc32(f"transformed/{p}".encode("utf-8")) & 0xFFFFFFFF] = (f"transformed/{p}", tr["m_LocalPosition"])
    t_crc[zlib.crc32(f"Reference/{p}".encode("utf-8")) & 0xFFFFFFFF] = (f"Reference/{p}", tr["m_LocalPosition"])
    for ch in tr["m_Children"]:
        walk_t(ch["m_PathID"], p)
for ch in rmap[t_tr_pid].read_typetree()["m_Children"]:
    walk_t(ch["m_PathID"], "")

# Print Ramjet Reference / COG local position
for crc, (p, pos) in sorted(t_crc.items(), key=lambda x: x[1][0]):
    if p in ("Reference", "Reference/COG"):
        print(f"  Ramjet {p}: m_LocalPosition={pos}")

# Check Starscream COG position in Skywarp
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"
es = UnityPy.load(str(SKYWARP))
smap = {o.path_id: o for o in es.objects}
for o in es.objects:
    if o.type.name == "GameObject" and o.read_typetree().get("m_Name") in ("Reference", "COG"):
        gtt = o.read_typetree()
        tr_pid = next((c["component"]["m_PathID"] for c in gtt["m_Component"] if smap[c["component"]["m_PathID"]].type.name == "Transform"), None)
        if tr_pid:
            print(f"  Skywarp '{gtt['m_Name']}' localPos={smap[tr_pid].read_typetree()['m_LocalPosition']}")

# Inspect Swoop_Vehicle_WingFlap_transformed using UnityPy AnimationClip typetree / raw curves
for o in em.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        print(f"\nSwoop clip '{tt['m_Name']}' dur={tt['m_MuscleClip']['m_StopTime']:.3f}s")
        for b in tt["m_ClipBindingConstant"]["genericBindings"]:
            p = t_crc.get(b["path"], (f"hash({b['path']})", None))[0]
            print(f"  path='{p}' attr={b['attribute']}")
