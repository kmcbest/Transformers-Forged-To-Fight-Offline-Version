import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SWOOP = ROOT / "assets_redeco/swoop_gs_deluxe2008.assetbundle"
e = UnityPy.load(str(SWOOP))
omap = {o.path_id: o for o in e.objects}

print("=== 1. Check transformed Avatar & Jet AOC ===")
av = omap[-5001927141424851882].read_typetree()
print("transformed Avatar name:", av["m_Name"], "humanSize:", av["m_Avatar"].get("m_Human", {}).get("m_RootX"))
print("  skeleton nodes:", len(av["m_Avatar"].get("m_AvatarSkeleton", {}).get("data", {}).get("m_Node", [])))
print("  m_TOS entries:", list(av.get("m_TOS", []))[:15])

jet_aoc = omap[-6340484879223379266].read_typetree()
print("Jet AOC m_Controller:", jet_aoc["m_Controller"])

print("\n=== 2. Check m_PreloadTable has FileID=3 PathID=7645321843667068633 ===")
ab = next(o.read_typetree() for o in e.objects if o.type.name == "AssetBundle")
p3 = [x["m_PathID"] for x in ab["m_PreloadTable"] if x["m_FileID"] == 3]
print("FileID=3 entries in m_PreloadTable:", len(p3), "contains 7645321843667068633?", 7645321843667068633 in p3)

print("\n=== 3. Check ALL Transform Scales inside Main Prefab 1529847556182042256 ===")
def walk_scales(go_pid, path=""):
    g = omap[go_pid].read_typetree()
    cur = f"{path}/{g['m_Name']}" if path else g["m_Name"]
    for c in g["m_Component"]:
        co = omap.get(c["component"]["m_PathID"])
        if co and co.type.name == "Transform":
            tr = co.read_typetree()
            sc = tr["m_LocalScale"]
            if sc["x"] < 0.01 or sc["y"] < 0.01 or sc["z"] < 0.01 or not g["m_IsActive"]:
                print(f"  ZERO/INACTIVE: {cur} active={g['m_IsActive']} scale=({sc['x']:.3f},{sc['y']:.3f},{sc['z']:.3f})")
            for ch in tr["m_Children"]:
                ch_go = omap[ch["m_PathID"]].read_typetree()["m_GameObject"]["m_PathID"]
                walk_scales(ch_go, cur)
walk_scales(1529847556182042256)
