import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def check_bundle_mesh(bundle_path):
    if not bundle_path.exists():
        return None
    env = UnityPy.load(str(bundle_path))
    meshes = {}
    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            name = tt.get("m_Name", "")
            aabb = tt.get("m_LocalAABB", {})
            c = aabb.get("m_Center", {})
            e = aabb.get("m_Extent", {})
            if c and e:
                y_min = c["y"] - e["y"]
                y_max = c["y"] + e["y"]
                h = y_max - y_min
                meshes[name] = (round(y_min, 3), round(y_max, 3), round(h, 3), round(c["y"], 3))
    return meshes

candidates = [
    ("Megatronus (Donor)", ROOT / "extracted_apk/assets/assetpack/megatronus_gs_kabam_odr/megatronus_gs_kabam.assetbundle"),
    ("Blast Off (Current)", ROOT / "assets_redeco/blastoff_gs.assetbundle"),
    ("Swindle", ROOT / "assets_redeco/swindle_gs.assetbundle"),
]

# Find any bundles for onslaught, brawl, vortex
for p in (ROOT / "assets_redeco").glob("*.assetbundle"):
    low = p.name.lower()
    if any(k in low for k in ("onslaught", "brawl", "vortex")):
        candidates.append((p.stem, p))

for label, p in candidates:
    res = check_bundle_mesh(p)
    print(f"\n=== {label} ({p.name}) ===")
    if res:
        for mname, (ymin, ymax, h, cy) in res.items():
            print(f"  Mesh: {mname:30s} | Y=[{ymin:+.3f}, {ymax:+.3f}] | Height={h:.3f} | CenterY={cy:.3f}")
    else:
        print("  Bundle not found or no meshes")
