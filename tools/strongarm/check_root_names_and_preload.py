import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

for label, p in [
    ("ONSLAUGHT", Path(r"E:\Agent\TFTF-blender\assets_redeco\onslaught_gs.assetbundle")),
    ("DEMOLISHOR", Path(r"E:\Agent\TFTF-blender\assets_redeco\demolishor_gs.assetbundle")),
    ("ELITA ONE", Path(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")),
]:
    env = UnityPy.load(str(p))
    gos = {o.path_id: o.read_typetree().get("m_Name") for o in env.objects if o.type.name == "GameObject"}
    trs = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "Transform"}
    roots = [gos[tr.get("m_GameObject", {}).get("m_PathID")] for tr in trs.values() if tr.get("m_Father", {}).get("m_PathID") == 0]
    print(f"{label} root GOs matching char/lw: {[r for r in roots if 'gs' in r.lower() or 'rotf' in r.lower() or 'deluxe' in r.lower()]}")

# Check Prowl Official AssetBundle m_PreloadTable entries matching victory or external #2
env_p = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
for o in env_p.objects:
    if o.type.name == "AssetBundle":
        ab = o.read_typetree()
        pt = ab.get("m_PreloadTable", [])
        f2 = [x.get("m_PathID") for x in pt if x.get("m_FileID") == 2]
        print(f"\nProwl Official m_PreloadTable len={len(pt)}, fileID=2 count={len(f2)}")
        print("  tactical_normal_victory (-2951149380490677767) in preload?", -2951149380490677767 in f2)
        print("  tactical_normal_Victory_idle (-9154018769279338152) in preload?", -9154018769279338152 in f2)
        f7 = [x.get("m_PathID") for x in pt if x.get("m_FileID") == 7]
        print(f"  fileID=7 (VictoryStagePrefab?) in preload: {f7}")

# Also check if Matinee_Prowl_Special03 or VictoryStage uses Prowl's victory clip
env_m = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\character_anim_procedural.assetbundle" if Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\character_anim_procedural.assetbundle").exists() else r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle")
for o in env_m.objects:
    if o.type.name == "AnimationClip":
        d = o.read()
        nm = getattr(d, 'name', '') or getattr(d, 'm_Name', '')
        if nm in ("tactical_normal_victory", "tactical_normal_Victory_idle", "Ultramagnus_Normal_victory", "Ultramagnus_Normal_victory_idle"):
            print(f"  Proc clip '{nm}': PathID={o.path_id}")
