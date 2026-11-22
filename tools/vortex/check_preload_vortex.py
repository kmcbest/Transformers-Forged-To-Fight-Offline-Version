import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

sys.path.insert(0, r"e:\Agent\TFTF-blender\tools")
import patch_vortex_melee as pvm

bundle_path = Path(r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

# Check all local PPtrs in SMRs, Materials, etc. AND check m_PreloadTable reachability
ab_tree = next(o for o in sf.objects.values() if o.type.name == "AssetBundle").read_typetree()
pt = ab_tree.get("m_PreloadTable", [])
for cname, cinfo in ab_tree.get("m_Container", []):
    pidx = int(cinfo["preloadIndex"])
    psize = int(cinfo["preloadSize"])
    sl = pt[pidx : pidx + psize]
    sl_set = {(int(x["m_FileID"]), int(x["m_PathID"])) for x in sl}
    reach = pvm.collect_reachable(sf, int(cinfo["asset"]["m_PathID"]))
    missing = reach - sl_set
    print(f"Container {cname}: preloadSize={psize}, reachable={len(reach)}, missing={missing}")
    assert not missing, f"Missing reachable PPtrs in PreloadTable: {missing}"

print("[PASS] All container PreloadTable entries cover 100% of reachable assets including new emblem & eye textures/materials!")
