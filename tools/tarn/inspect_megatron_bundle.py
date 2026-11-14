import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(BUNDLE))

print("=== BUNDLE SUMMARY ===")
print("CAB:", [f.name for f in env.files.values() if hasattr(f, "name")])
for o in env.objects:
    if o.type.name == "AssetBundle":
        ab = o.read_typetree()
        print("m_AssetBundleName:", ab.get("m_AssetBundleName"))
        print("m_Container keys:", [x[0] for x in ab.get("m_Container", [])])

go_dict = {}
tr_dict = {}
tr_to_go = {}
go_to_tr = {}
for o in env.objects:
    if o.type.name == "GameObject":
        go_dict[o.path_id] = o.read_typetree()
    elif o.type.name == "Transform":
        t = o.read_typetree()
        tr_dict[o.path_id] = t
        gid = t["m_GameObject"]["m_PathID"]
        tr_to_go[o.path_id] = gid
        go_to_tr[gid] = o.path_id

print("\n=== ROOT GAMEOBJECTS ===")
for gid, go in go_dict.items():
    tid = go_to_tr.get(gid)
    if tid and tr_dict[tid]["m_Father"]["m_PathID"] == 0:
        print(f"  Root GO: {go['m_Name']} | PathID={gid} | TransformID={tid}")

print("\n=== MESHES ===")
for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        c = m["m_LocalAABB"]["m_Center"]
        e = m["m_LocalAABB"]["m_Extent"]
        print(f"  Mesh: {m['m_Name']:45s} | PID={o.path_id:21d} | verts={m['m_VertexData']['m_VertexCount']:5d} | submeshes={len(m['m_SubMeshes'])} | bones={len(m['m_BindPose']):2d} | hashes={len(m.get('m_BoneNameHashes',[])):2d} | center=({c['x']:.2f},{c['y']:.2f},{c['z']:.2f}) ext=({e['x']:.2f},{e['y']:.2f},{e['z']:.2f})")

print("\n=== SKINNED MESH RENDERERS ===")
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        s = o.read_typetree()
        gid = s["m_GameObject"]["m_PathID"]
        gname = go_dict.get(gid, {}).get("m_Name", "")
        c = s["m_AABB"]["m_Center"]
        e = s["m_AABB"]["m_Extent"]
        mats = [m["m_PathID"] for m in s["m_Materials"]]
        print(f"  SMR: {gname:45s} | PID={o.path_id:21d} | mesh={s['m_Mesh']['m_PathID']} | bones={len(s['m_Bones']):2d} | mats={mats} | center=({c['x']:.2f},{c['y']:.2f},{c['z']:.2f})")

print("\n=== MATERIALS ===")
for o in env.objects:
    if o.type.name == "Material":
        m = o.read_typetree()
        texs = {k: (v["m_Texture"]["m_PathID"], v["m_Scale"], v["m_Offset"]) for k, v in m["m_SavedProperties"]["m_TexEnvs"] if v["m_Texture"]["m_PathID"] != 0}
        print(f"  Mat: {m['m_Name']:42s} | PID={o.path_id:21d} | texs={texs}")

print("\n=== TEXTURE2D ===")
for o in env.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        print(f"  Tex: {t.m_Name:40s} | PID={o.path_id:21d} | {t.m_Width}x{t.m_Height} | fmt={t.m_TextureFormat}")

print("\n=== ANIMATION CLIPS & AOC ===")
for o in env.objects:
    if o.type.name == "AnimationClip":
        c = o.read_typetree()
        print(f"  Clip: {c['m_Name']:45s} | len={c['m_MuscleClip']['m_StopTime']:.2f}s | PID={o.path_id}")
    elif o.type.name == "AnimatorOverrideController":
        aoc = o.read_typetree()
        print(f"  AOC: {aoc['m_Name']} | overrides={len(aoc.get('m_Clips', []))}")
