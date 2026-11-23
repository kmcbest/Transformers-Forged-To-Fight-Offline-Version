import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

# Check Motormaster Gun actual bounds in LeftHand space using m_LocalAABB & transforms
# In MM:
# gun TR: pos=(-0.133, -0.72, 0), rot=identity (plus PropsCtrl Pos=(-0.133, -0.72, 0))
# child cha_motormaster... TR: pos=(-1.04534, 0.30061, 1.47442), rot=(0,0,-0.707106,0.707107) [euler Z=-90]
# child mesh m_LocalAABB: center=(0, -1.3845, -0.4816), extent=(0.477, 2.949, 1.452)
# Notice in StarSaber: gun TR pos = (-0.80, -0.8073, 2.5779), rot=(0, -90 deg Y, 0)
# Wait: why did StarSaber put RotationOffset=(0, -90, 0) when Motormaster had RotationOffset=(0,0,0)? Because MM's LeftHand clip or gun clip rotates it!
# Let's check MM's Motormaster Gun AOC (105235449740021664) & handGun_L_attackRanged_01 LeftHand bone rotation!
mm_env = UnityPy.load(str(ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle"))
mm_map = {o.path_id: o for o in mm_env.objects}
aoc = mm_map[105235449740021664].read_typetree()
print("=== Motormaster Gun AOC ===")
for i, c in enumerate(aoc["m_Clips"]):
    ovr = c["m_OverrideClip"]
    if ovr["m_PathID"] != 0 and ovr["m_PathID"] != c["m_OriginalClip"]["m_PathID"]:
        nm = mm_map[ovr["m_PathID"]].read_typetree().get("m_Name", "") if ovr["m_FileID"]==0 and ovr["m_PathID"] in mm_map else ""
        print(f"  [{i}] orig=({c['m_OriginalClip']['m_FileID']},{c['m_OriginalClip']['m_PathID']}) -> ({ovr['m_FileID']},{ovr['m_PathID']}) '{nm}'")

# Also inspect Windblade & Sideswipe & Mixmaster full PrefabList for our missing FX names!
cfx = UnityPy.load(str(ROOT_BL / "assets_netflix" / "character_fx.assetbundle"))
cfx_names = {o.read_typetree().get("m_Name", ""): o.path_id for o in cfx.objects if o.type.name == "GameObject"}
cfx_p = UnityPy.load(str(ROOT_BL / "assets_netflix" / "character_fx_procedural.assetbundle"))
cfxp_names = {o.read_typetree().get("m_Name", ""): o.path_id for o in cfx_p.objects if o.type.name == "GameObject"}

for nm in ("fx_p_special_projectile_impact", "fx_l_hit_small_perceptual_orange", "fx_l_hit_medium_perceptual", "fx_r_trail_white", "fx_p_megatron_gs_muzzle_flash", "fx_p_tank_megatron_gs_purple_muzzle_small"):
    print(f"  FX '{nm}': cfx={cfx_names.get(nm, '-')}, cfx_p={cfxp_names.get(nm, '-')}")
