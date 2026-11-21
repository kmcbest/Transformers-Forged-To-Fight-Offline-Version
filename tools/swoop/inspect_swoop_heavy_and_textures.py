import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import zlib
import UnityPy
from pathlib import Path
from PIL import Image

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
PROC = TFTF / "extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle"
MESH_BUNDLE = ROOT / "toolchain/unity_build_project/AssetBundles/swoop_mesh.assetbundle"

print("=== 1. Inspect Ramjet m_Externals ===")
er = UnityPy.load(str(RAMJET))
sf_r = list(er.assets)[0]
for idx, ext in enumerate(sf_r.externals):
    print(f"  External[{idx+1}]: path='{ext.path}', temp='{ext.temp_empty}'")

print("\n=== 2. Inspect StarScream_Normal_attackHeavy & transformed bindings ===")
ep = UnityPy.load(str(PROC))
pmap = {o.path_id: o for o in ep.objects}

# Check Ramjet Transform names to crc32 hashes so we can decode AnimationClip binding path hashes!
hash_to_path = {}
rmap = {o.path_id: o for o in er.objects}
# Find root GO 1529847556182042256
def walk_tr(tr_pid, prefix=""):
    tr_tt = rmap[tr_pid].read_typetree()
    go_pid = tr_tt["m_GameObject"]["m_PathID"]
    go_name = rmap[go_pid].read_typetree()["m_Name"]
    path = f"{prefix}/{go_name}" if prefix else ""
    if path:
        path_rel = path.lstrip("/")
        crc = zlib.crc32(path_rel.encode("utf-8")) & 0xFFFFFFFF
        hash_to_path[crc] = path_rel
    for ch in tr_tt["m_Children"]:
        walk_tr(ch["m_PathID"], path if path else "")

root_go = rmap[1529847556182042256].read_typetree()
for comp in root_go["m_Component"]:
    cobj = rmap.get(comp["component"]["m_PathID"])
    if cobj and cobj.type.name == "Transform":
        tr_tt = cobj.read_typetree()
        for ch in tr_tt["m_Children"]:
            walk_tr(ch["m_PathID"], "")
        break

print(f"Built {len(hash_to_path)} CRC paths from Ramjet hierarchy.")

for label, cpid in [
    ("StarScream_Normal_attackHeavy", 7645321843667068633),
    ("StarScream_Normal_attackHeavy_transformed", -7989888022101248653),
]:
    tt = pmap[cpid].read_typetree()
    print(f"\n--- Clip '{tt['m_Name']}' (dur={tt['m_MuscleClip']['m_StopTime']:.3f}s) ---")
    gen = tt["m_ClipBindingConstant"]["genericBindings"]
    print(f"  genericBindings ({len(gen)}):")
    for b in gen[:40]:
        p = hash_to_path.get(b["path"], f"hash({b['path']})")
        print(f"    path='{p}', attr={b.get('attribute')}, typeID={b.get('typeID')}, customType={b.get('customType')}")

print("\n=== 3. Compare cha_swoop_main_RAOE vs cha_swoop_vh_RAOE & check textures ===")
for name in [
    "cha_swoop_main_Diffuse.png",
    "cha_swoop_main_Normal_unity.png",
    "cha_swoop_main_RAOE.png",
    "cha_swoop_vh_Diffuse.png",
    "cha_swoop_vh_Normal_unity.png",
    "cha_swoop_vh_RAOE.png",
]:
    p = ROOT / "3rd-party-models/swoop/02_textures" / name
    im = Image.open(p)
    print(f"  {name}: size={im.size}, mode={im.mode}, extrema={im.getextrema()}")

print("\n=== 4. Inspect Swoop_Vehicle_WingFlap_transformed in swoop_mesh.assetbundle ===")
em = UnityPy.load(str(MESH_BUNDLE))
for o in em.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        print(f"  Clip '{tt['m_Name']}': dur={tt['m_MuscleClip']['m_StopTime']:.3f}s, wrap={tt['m_WrapMode']}, bindings={len(tt['m_ClipBindingConstant']['genericBindings'])}")
        for b in tt["m_ClipBindingConstant"]["genericBindings"][:15]:
            p = hash_to_path.get(b["path"], f"hash({b['path']})")
            print(f"    path='{p}', attr={b.get('attribute')}, typeID={b.get('typeID')}")
    elif o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"  Mesh '{tt['m_Name']}': boneHashes={len(tt['m_BoneNameHashes'])}, bindPose={len(tt['m_BindPose'])}")
