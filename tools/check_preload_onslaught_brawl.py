import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

sys.path.insert(0, r"e:\Agent\TFTF-blender\tools")
from patch_vortex_melee import collect_reachable, rebuild_container_preload_table

for name in ["onslaught_gs.assetbundle", "brawl_gs.assetbundle"]:
    bpath = Path(r"e:\Agent\TFTF-blender\assets_redeco") / name
    env = UnityPy.load(str(bpath))
    sf = list(env.assets)[0]
    ab_tree = next(o for o in sf.objects.values() if o.type.name == "AssetBundle").read_typetree()
    pt = ab_tree.get("m_PreloadTable", [])
    needs_fix = False
    for cname, cinfo in ab_tree.get("m_Container", []):
        pidx, psize = int(cinfo["preloadIndex"]), int(cinfo["preloadSize"])
        sl_set = {(int(x["m_FileID"]), int(x["m_PathID"])) for x in pt[pidx : pidx + psize]}
        reach = collect_reachable(sf, int(cinfo["asset"]["m_PathID"]))
        missing = reach - sl_set
        if missing:
            print(f"[FIX NEEDED] {name} Container {cname} missing {len(missing)} PPtrs: {missing}")
            needs_fix = True
        else:
            print(f"[PASS] {name} Container {cname}: PreloadTable complete ({psize})")
    if needs_fix:
        rebuild_container_preload_table(sf)
        out_bytes = env.file.save(packer="lz4")
        with open(bpath, "wb") as f:
            f.write(out_bytes)
        print(f"[✓] Fixed PreloadTable & saved {bpath} ({len(out_bytes):,} bytes)")
