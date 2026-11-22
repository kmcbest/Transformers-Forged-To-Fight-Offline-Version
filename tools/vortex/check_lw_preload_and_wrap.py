import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import sys as _sys
_sys.path.insert(0, r"e:\Agent\TFTF-blender\tools")
from patch_vortex_melee import collect_reachable

env = UnityPy.load(r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle")
sf = list(env.assets)[0]
ab_tree = next(o for o in sf.objects.values() if o.type.name == "AssetBundle").read_typetree()

print("=== Preload check ===")
for cname, cinfo in ab_tree["m_Container"]:
    pidx, psize = cinfo["preloadIndex"], cinfo["preloadSize"]
    root_pid = cinfo["asset"]["m_PathID"]
    reach = collect_reachable(sf, root_pid)
    sl = ab_tree["m_PreloadTable"][pidx : pidx + psize]
    sl_set = {(x["m_FileID"], x["m_PathID"]) for x in sl}
    print(f"  {cname}: root={root_pid}, pt_len={len(sl)}, reach={len(reach)}, missing={reach - sl_set}")

print("\n=== Texture WrapModes ===")
for pid in [5741437468734501436, -3179261496129805109, 696671028566742258, 6239694728433603131]:
    tt = sf.objects[pid].read_typetree()
    print(f"  Tex {tt['m_Name']} ({pid}): WrapU={tt['m_TextureSettings']['m_WrapU']}, WrapV={tt['m_TextureSettings']['m_WrapV']}")
