import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import math
import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

# Helper: quaternion & 4x4 matrix math
def q_to_m3(q):
    x, y, z, w = q["x"], q["y"], q["z"], q["w"]
    return [
        [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
        [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)],
    ]

def tr_to_m4(tr):
    r = q_to_m3(tr["m_LocalRotation"])
    p = tr["m_LocalPosition"]
    s = tr["m_LocalScale"]
    return [
        [r[0][0]*s["x"], r[0][1]*s["y"], r[0][2]*s["z"], p["x"]],
        [r[1][0]*s["x"], r[1][1]*s["y"], r[1][2]*s["z"], p["y"]],
        [r[2][0]*s["x"], r[2][1]*s["y"], r[2][2]*s["z"], p["z"]],
        [0, 0, 0, 1],
    ]

def bp_to_m4(bp):
    return [
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
    ]

def m4_mul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def m4_pt(M, p):
    return (
        M[0][0]*p[0] + M[0][1]*p[1] + M[0][2]*p[2] + M[0][3],
        M[1][0]*p[0] + M[1][1]*p[1] + M[1][2]*p[2] + M[1][3],
        M[2][0]*p[0] + M[2][1]*p[1] + M[2][2]*p[2] + M[2][3],
    )

# 1. Compute Windblade RightHand -> Sword World Space (local to RightHand)
wb_env = UnityPy.load(str(ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle"))
wb_map = {o.path_id: o for o in wb_env.objects}
# Windblade Sword TRs: Sword(4596292760489948128) -> Reference(-2020770388260780493) -> COG(-8941191178826677062)
wb_sword = tr_to_m4(wb_map[4596292760489948128].read_typetree())
wb_ref = tr_to_m4(wb_map[-2020770388260780493].read_typetree())
wb_cog = tr_to_m4(wb_map[-8941191178826677062].read_typetree())
wb_mesh_tt = wb_map[-5419018504334982301].read_typetree()
wb_bp = bp_to_m4(wb_mesh_tt["m_BindPose"][0])
# Vertex in Mesh space -> Bone COG space via BindPose^-1 (Wait: SkinnedMesh: M_bone_in_root * BindPose * v_mesh!)
M_wb = m4_mul(m4_mul(wb_sword, wb_ref), m4_mul(wb_cog, wb_bp))
print("=== Windblade Sword Mesh -> RightHand Matrix ===")
for row in M_wb:
    print(" ", [round(x, 4) for x in row])
# Map mesh origin (0,0,0), tip (0,0,6.5), edge (0,1,0), flat (1,0,0)
print("  Windblade tip  (0,0,6.5) -> RightHand:", [round(x, 3) for x in m4_pt(M_wb, (0,0,6.5))])
print("  Windblade hilt (0,0,-0.4)-> RightHand:", [round(x, 3) for x in m4_pt(M_wb, (0,0,-0.4))])
print("  Windblade +Y (edge dir)  -> RightHand:", [round(x - M_wb[i][3], 3) for i, x in enumerate(m4_pt(M_wb, (0,1,0)))])
print("  Windblade +X (flat dir)  -> RightHand:", [round(x - M_wb[i][3], 3) for i, x in enumerate(m4_pt(M_wb, (1,0,0)))])

# 2. Compute Bludgeon RightHand -> Sword Space
bld_env = UnityPy.load(str(ROOT_GM / "extracted_apk/assets/assetpack/bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle"))
bld_map = {o.path_id: o for o in bld_env.objects}
# Find Bludgeon sword TRs
for o in bld_env.objects:
    if o.type.name == "GameObject" and o.read_typetree().get("m_Name") == "sword":
        sword_go = o.read_typetree()
        s_tr = next(c["component"]["m_PathID"] for c in sword_go["m_Component"] if bld_map[c["component"]["m_PathID"]].type.name == "Transform")
        s_tt = bld_map[s_tr].read_typetree()
        print("\n=== Bludgeon Sword Children ===")
        for ch in s_tt["m_Children"]:
            ch_tt = bld_map[ch["m_PathID"]].read_typetree()
            go_nm = bld_map[ch_tt["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"]
            print(f"  child '{go_nm}' TR={ch['m_PathID']}")
        break
bld_sword = tr_to_m4(bld_map[s_tr].read_typetree())
# Ref=5727911922954392913, COG=6385818638844004440
bld_ref = tr_to_m4(bld_map[5727911922954392913].read_typetree())
bld_cog = tr_to_m4(bld_map[6385818638844004440].read_typetree())
bld_mesh_tt = bld_map[-6021306196609584054].read_typetree()
bld_bp = bp_to_m4(bld_mesh_tt["m_BindPose"][0])
M_bld = m4_mul(m4_mul(bld_sword, bld_ref), m4_mul(bld_cog, bld_bp))
print("=== Bludgeon Sword Mesh -> RightHand Matrix ===")
for row in M_bld:
    print(" ", [round(x, 4) for x in row])
print("  Bludgeon tip  (0,0,7.5) -> RightHand:", [round(x, 3) for x in m4_pt(M_bld, (0,0,7.5))])
print("  Bludgeon hilt (0,0,-1.5)-> RightHand:", [round(x, 3) for x in m4_pt(M_bld, (0,0,-1.5))])
print("  Bludgeon +Y             -> RightHand:", [round(x - M_bld[i][3], 3) for i, x in enumerate(m4_pt(M_bld, (0,1,0)))])
print("  Bludgeon +X             -> RightHand:", [round(x - M_bld[i][3], 3) for i, x in enumerate(m4_pt(M_bld, (1,0,0)))])

# Inspect Bludgeon clip 8402833034577814384
bld_clip = bld_map[8402833034577814384].read_typetree()
print(f"\n=== Bludgeon S2 Sword Clip: '{bld_clip['m_Name']}' ===")
print(f"  MuscleClip start={bld_clip['m_MuscleClip']['m_StartTime']:.3f} stop={bld_clip['m_MuscleClip']['m_StopTime']:.3f}")
clip_data = bld_clip["m_MuscleClip"]["m_Clip"]
bindings = bld_clip.get("m_ClipBindingConstant", {}).get("genericBindings", [])
print(f"  genericBindings count={len(bindings)}: {[(b['path'], b['attribute']) for b in bindings[:10]]}")

# 3. Check character_fx.assetbundle & character_fx_procedural.assetbundle for required FX
cfx = UnityPy.load(str(ROOT_BL / "assets_netflix" / "character_fx.assetbundle"))
cfx_names = {}
for o in cfx.objects:
    if o.type.name == "GameObject":
        cfx_names[o.read_typetree().get("m_Name", "")] = o.path_id

cfx_p = UnityPy.load(str(ROOT_BL / "assets_netflix" / "character_fx_procedural.assetbundle"))
cfxp_names = {}
for o in cfx_p.objects:
    if o.type.name == "GameObject":
        cfxp_names[o.read_typetree().get("m_Name", "")] = o.path_id

req_fx = [
    "fx_p_red_projectile", "fx_p_red_projectile_impact", "fx_p_optimus_muzzle_flash", "fx_l_hit_small_perceptual",
    "fx_p_special_projectile", "fx_p_mixmaster_gun_fire_special", "fx_p_grimlock_scrape_sparks",
    "fx_p_acid_spray", "fx_p_tank_muzzle_flash", "fx_p_tank_muzzle_small", "fx_p_tank_shell_hit",
    "fx_p_windblade_radius", "fx_p_scrape_sparks", "fx_p_hit_large_no_local",
    "fx_p_missile_projectile_impact", "fx_p_missile_smoke", "fx_p_rocket_fire", "fx_p_scorponok_missile_small_fire", "fx_p_projectile_blur",
    "fx_p_land_dust", "fx_p_foot_drag_sparks", "fx_p_hit_punch_sparks_special", "fx_p_hit_small", "fx_p_hit_medium",
]
print("\n=== Required FX Locations (cfx=FileID? vs cfx_p vs local) ===")
for nm in req_fx:
    print(f"  {nm:<36} | cfx={cfx_names.get(nm, '-')} | cfx_p={cfxp_names.get(nm, '-')}")
