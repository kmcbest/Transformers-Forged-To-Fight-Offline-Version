import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

RAMJET = TFTF / "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle"
PROC = TFTF / "extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle"
MESH_BUNDLE = ROOT / "toolchain/unity_build_project/AssetBundles/swoop_mesh.assetbundle"

ep = UnityPy.load(str(PROC))
clip_lookup = {}
for o in ep.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        clip_lookup[o.path_id] = (tt.get("m_Name", ""), tt.get("m_MuscleClip", {}).get("m_StopTime", 0))

er = UnityPy.load(str(RAMJET))
rmap = {o.path_id: o for o in er.objects}
for o in er.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        clip_lookup[o.path_id] = (tt.get("m_Name", ""), tt.get("m_MuscleClip", {}).get("m_StopTime", 0))

print("=== 1. Ramjet Jet AOC (-6340484879223379266) & LW AOC (3988326131143923314) ===")
for aoc_pid in [-6340484879223379266, 3988326131143923314, -7199814496945827738, 9141045697105876260]:
    tt = rmap[aoc_pid].read_typetree()
    print(f"\nAOC '{tt.get('m_Name')}' PID={aoc_pid}:")
    for i, c in enumerate(tt.get("m_Clips", [])):
        opid = c["m_OriginalClip"]["m_PathID"]
        cpid = c["m_OverrideClip"]["m_PathID"]
        oname = clip_lookup.get(opid, (f"({opid})", 0))[0]
        cname, cdur = clip_lookup.get(cpid, (f"({cpid})", 0))
        if opid != 0 or cpid != 0:
            print(f"  [{i:2d}] orig='{oname}' -> ovr='{cname}' (PID={cpid}, dur={cdur:.2f}s)")

print("\n=== 2. Ramjet Meshes boneNameHashes & BindPose vs swoop_mesh ===")
em = UnityPy.load(str(MESH_BUNDLE))
mm = {o.read_typetree()["m_Name"]: o.read_typetree() for o in em.objects if o.type.name == "Mesh"}
for rpid, skey in [(8801638638334271379, "cha_swoop_gs_00"), (733405694182770835, "cha_swoop_gs_01")]:
    rtt = rmap[rpid].read_typetree()
    stt = mm[skey]
    print(f"\nMesh {skey} vs Ramjet {rtt['m_Name']}:")
    print(f"  Ramjet: boneHashes={len(rtt['m_BoneNameHashes'])}, bindPose={len(rtt['m_BindPose'])}, rootHash={rtt['m_RootBoneNameHash']}, verts={rtt['m_VertexData']['m_VertexCount']}, subs={len(rtt['m_SubMeshes'])}")
    print(f"  Swoop:  boneHashes={len(stt['m_BoneNameHashes'])}, bindPose={len(stt['m_BindPose'])}, rootHash={stt['m_RootBoneNameHash']}, verts={stt['m_VertexData']['m_VertexCount']}, subs={len(stt['m_SubMeshes'])}")
    # Also print bounding box of Swoop mesh!
    c = stt["m_LocalAABB"]["m_Center"]
    ex = stt["m_LocalAABB"]["m_Extent"]
    print(f"  Swoop AABB: center=({c['x']:.3f}, {c['y']:.3f}, {c['z']:.3f}), extent=({ex['x']:.3f}, {ex['y']:.3f}, {ex['z']:.3f})")
    rc = rtt["m_LocalAABB"]["m_Center"]
    rex = rtt["m_LocalAABB"]["m_Extent"]
    print(f"  Ramjet AABB: center=({rc['x']:.3f}, {rc['y']:.3f}, {rc['z']:.3f}), extent=({rex['x']:.3f}, {rex['y']:.3f}, {rex['z']:.3f})")

print("\n=== 3. Check Shader names of Ramjet's Materials ===")
for mpid in [1469909421462177924, 3520121911555544087, -6074135333607175177, 3595971348910711679]:
    mtt = rmap[mpid].read_typetree()
    spid = mtt["m_Shader"]["m_PathID"]
    sfile = mtt["m_Shader"]["m_FileID"]
    print(f"  Mat PID={mpid}: shader FileID={sfile}, PathID={spid}")
