import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

MESH_BUNDLE = ROOT / "toolchain/unity_build_project/AssetBundles/swoop_mesh.assetbundle"
SWOOP = ROOT / "assets_redeco/swoop_gs_deluxe2008.assetbundle"
RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"

em = UnityPy.load(str(MESH_BUNDLE))
mmap = {o.path_id: o for o in em.objects}

print("=== swoop_mesh.assetbundle Objects ===")
for o in em.objects:
    tt = o.read_typetree()
    if o.type.name == "Mesh":
        print(f"Mesh '{tt['m_Name']}' PID={o.path_id}: bindPose0={tt['m_BindPose'][0] if tt['m_BindPose'] else None}")
    elif o.type.name == "SkinnedMeshRenderer":
        mpid = tt["m_Mesh"]["m_PathID"]
        mname = mmap[mpid].read_typetree()["m_Name"]
        bones = [mmap[mmap[b["m_PathID"]].read_typetree()["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"] for b in tt["m_Bones"]]
        print(f"SMR for '{mname}' (bones={len(bones)}): {bones[:10]}...")

es = UnityPy.load(str(SWOOP))
smap = {o.path_id: o for o in es.objects}
print("\n=== swoop_gs_deluxe2008.assetbundle SMRs & BindPose compare ===")
for label, spid, mpid in [("Robot _00", -3606013326717668247, 8801638638334271379), ("Vehicle _01", 4450385079657545705, 733405694182770835)]:
    stt = smap[spid].read_typetree()
    mtt = smap[mpid].read_typetree()
    bones = [smap[smap[b["m_PathID"]].read_typetree()["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"] for b in stt["m_Bones"]]
    print(f"{label}: SMR bones={len(bones)} -> {bones[:8]}...")
    print(f"  Mesh bindPose[0]={mtt['m_BindPose'][0]}")
