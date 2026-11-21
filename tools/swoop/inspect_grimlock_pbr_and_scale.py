import sys
import numpy as np
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

grim_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle"
env = UnityPy.load(grim_path)
objs = {o.path_id: o for o in env.objects}

print("=== Official Grimlock Materials & Textures ===")
tex_stats_done = set()
for o in env.objects:
    if o.type.name == "Material":
        m = o.read_typetree()
        floats = dict(m["m_SavedProperties"]["m_Floats"])
        cols = dict(m["m_SavedProperties"]["m_Colors"])
        envs = {k: v["m_Texture"]["m_PathID"] for k, v in m["m_SavedProperties"]["m_TexEnvs"]}
        if "_base_tex" in envs:
            print(f"\nMat '{m['m_Name']}' ({o.path_id}):")
            for k in ("_Mode", "_metallic_range", "_roughness_range", "_clearcoat_reflectance_range", "_emissive_overbright_range", "_emissive_range"):
                print(f"  {k} = {floats.get(k)}")
            for k in ("_Color", "_base_col", "_emissive_intensity_col"):
                print(f"  {k} = {cols.get(k)}")
            for prop, tpid in envs.items():
                if tpid in objs and tpid not in tex_stats_done and prop in ("_base_tex", "_normal_tex", "_pbr_composite_tex"):
                    tex_stats_done.add(tpid)
                    t = objs[tpid].read()
                    try:
                        im = t.image.convert("RGB")
                        arr = np.array(im, dtype=np.float32)
                        lum = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
                        print(f"  Tex {prop} '{t.m_Name}' ({im.size}, fmt={t.m_TextureFormat}):")
                        for ci, cname in enumerate(("R", "G", "B")):
                            c = arr[:, :, ci]
                            print(f"    ch[{cname}]: mean={c.mean():.1f}, p10={np.percentile(c,10):.1f}, p50={np.percentile(c,50):.1f}, p90={np.percentile(c,90):.1f}, max={c.max():.1f}")
                        if prop == "_base_tex":
                            sat = (arr.max(axis=2) - arr.min(axis=2)) / np.maximum(arr.max(axis=2), 1.0)
                            print(f"    lum: mean={lum.mean():.1f}, p10={np.percentile(lum,10):.1f}, p50={np.percentile(lum,50):.1f}, p90={np.percentile(lum,90):.1f}, sat_mean={sat.mean():.3f}")
                    except Exception as e:
                        print(f"  Tex {prop} decode err: {e}")

# Also check Grimlock _00 & _01 Mesh bounds for scale comparison, and check Swoop Jet AOC for any Reference scale curves
for smr_name in ("cha_grimlock_gs_mp08_00", "cha_grimlock_gs_mp08_01"):
    for o in env.objects:
        if o.type.name == "Mesh" and smr_name[:12] in o.read().m_Name:
            mt = o.read_typetree()
            print(f"\nGrimlock Mesh '{mt['m_Name']}': center={mt['m_LocalAABB']['m_Center']}, extent={mt['m_LocalAABB']['m_Extent']}")

# Check Swoop bundle: does ANY clip in Jet AOC animate Reference scale?
senv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")
so = {o.path_id: o for o in senv.objects}
print("\n=== Checking Swoop Reference (-6891910190203298850) Transform & Jet AOC ===")
ref_tr = so[-6891910190203298850].read_typetree()
print("Reference Transform:", ref_tr["m_LocalPosition"], ref_tr["m_LocalRotation"], ref_tr["m_LocalScale"])
cog_tr = so[6685185338456762215].read_typetree()
print("COG Transform:", cog_tr["m_LocalPosition"], cog_tr["m_LocalRotation"], cog_tr["m_LocalScale"])
smr_tr = so[-6460594894067674067].read_typetree()
print("cha_ramjet_gs_deluxe2008_01 Transform:", smr_tr["m_LocalPosition"], smr_tr["m_LocalRotation"], smr_tr["m_LocalScale"])
