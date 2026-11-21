import sys
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")
objs = {o.path_id: o for o in env.objects}

# 1. Walk parent chain of transformed (7693429312995989932) and cha_swoop_gs_01 SMR (4450385079657545705)
def show_ancestors(tr_pid, label):
    print(f"=== Ancestors of {label} (tr={tr_pid}) ===")
    cur = tr_pid
    while cur and cur in objs:
        tr = objs[cur].read_typetree()
        go = objs[tr["m_GameObject"]["m_PathID"]].read_typetree()
        print(f"  GO '{go['m_Name']}' active={go['m_IsActive']} pos={tr['m_LocalPosition']} rot={tr['m_LocalRotation']} scale={tr['m_LocalScale']}")
        cur = tr["m_Father"]["m_PathID"]

smr = objs[4450385079657545705].read_typetree()
show_ancestors(smr["m_GameObject"]["m_PathID"] and [c["component"]["m_PathID"] for c in objs[smr["m_GameObject"]["m_PathID"]].read_typetree()["m_Component"] if objs[c["component"]["m_PathID"]].type.name=="Transform"][0], "cha_swoop_gs_01")

# 2. Check ALL 29 bindposes of cha_swoop_gs_01 vs Donor Ramjet
renv = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
robjs = {o.path_id: o for o in renv.objects}
r_mesh = robjs[733405694182770835].read_typetree()
s_mesh = objs[733405694182770835].read_typetree()

print("\n=== All 29 BindPoses translation diff vs Donor ===")
max_dt = 0.0
for i, (sb, rb) in enumerate(zip(s_mesh["m_BindPose"], r_mesh["m_BindPose"])):
    dt = ((sb["e03"]-rb["e03"])**2 + (sb["e13"]-rb["e13"])**2 + (sb["e23"]-rb["e23"])**2)**0.5
    max_dt = max(max_dt, dt)
    if dt > 0.01:
        print(f"  [{i}] dt={dt:.4f}")
print(f"  max translation diff across 29 bones = {max_dt:.6f}")

# 3. Check if any BoneWeights in swoop_mesh use invalid bone indices (>= 29)
sm_obj = objs[733405694182770835].read()
skin = sm_obj.m_Skin
if skin:
    bad_idx = [bw for bw in skin if any(idx >= 29 or idx < 0 for idx in bw.boneIndex)]
    zero_w = [bw for bw in skin if sum(bw.weight) < 0.01]
    print(f"  m_Skin len={len(skin)}, bad_idx={len(bad_idx)}, zero_w={len(zero_w)}")
else:
    print("  m_Skin is empty (Unity 2019+ uses m_BonesPerVertex + weights or VertexData)")

# 4. Check MAT_VEHICLE_PID vs Donor MAT_VEHICLE_PID
r_mat = robjs[3520121911555544087].read_typetree()
s_mat = objs[3520121911555544087].read_typetree()
print("\n=== MAT_VEHICLE_PID floats & colors ===")
print("  Shader:", s_mat["m_Shader"], "Donor:", r_mat["m_Shader"])
print("  Floats:", s_mat["m_SavedProperties"]["m_Floats"])
print("  Colors:", s_mat["m_SavedProperties"]["m_Colors"])
print("  TexEnvs:", {k: v["m_Texture"] for k, v in s_mat["m_SavedProperties"]["m_TexEnvs"]})
print("  ShaderKeywords:", s_mat.get("m_ShaderKeywords"))
print("  CustomRenderQueue:", s_mat.get("m_CustomRenderQueue"))
