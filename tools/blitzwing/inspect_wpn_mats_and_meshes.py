import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

# 1. Megatron original materials
meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
omap = {o.path_id: o for o in meg_env.objects}
print("=== Megatron Original Materials ===")
for o in meg_env.objects:
    if o.type.name == "Material":
        m = o.read_typetree()
        envs = {k: (v["m_Texture"]["m_PathID"], omap[v["m_Texture"]["m_PathID"]].read().m_Name if v["m_Texture"]["m_PathID"] in omap else 0)
                for k, v in m["m_SavedProperties"]["m_TexEnvs"] if v["m_Texture"]["m_PathID"] != 0}
        if envs:
            print(f"  Mat {o.path_id} '{m['m_Name']}': {envs}")

# 2. Motormaster Gun, Bludgeon Sword, Windblade Sword mesh localAABB + bindpose + Bludgeon Sword AOC
for label, bpath, smr_pid in [
    ("Motormaster Gun", ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle", 7221289959388044615),
    ("Bludgeon Sword", ROOT_GM / "extracted_apk/assets/assetpack/bludgeon_gs_rd20_odr/bludgeon_gs_rd20.assetbundle", -2658441636626109797),
    ("Windblade Sword", ROOT_GM / "extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle", 2054443761467557922),
]:
    env = UnityPy.load(str(bpath))
    m = {o.path_id: o for o in env.objects}
    if smr_pid in m:
        smr = m[smr_pid].read_typetree()
        mpid = smr["m_Mesh"]["m_PathID"]
        mesh = m[mpid].read_typetree()
        print(f"\n=== {label} ===")
        print(f"  Mesh '{mesh['m_Name']}' ({mpid}) localAABB={mesh['m_LocalAABB']} verts={mesh['m_VertexData']['m_VertexCount']} bones={len(mesh['m_BindPose'])}")
        print(f"  BindPose[0]={mesh['m_BindPose'][0] if mesh['m_BindPose'] else None}")
        print(f"  SMR bones={len(smr['m_Bones'])}, rootBone={smr['m_RootBone']}")
    if "Bludgeon" in label:
        aoc = m[6154578337812704533].read_typetree()
        print(f"  Bludgeon Sword AOC '{aoc['m_Name']}':")
        for i, c in enumerate(aoc["m_Clips"]):
            orig = c["m_OriginalClip"]["m_PathID"]
            ovr = c["m_OverrideClip"]["m_PathID"]
            if orig != 0 and ovr != orig:
                nm = m[ovr].read_typetree().get("m_Name", "") if (c["m_OverrideClip"]["m_FileID"]==0 and ovr in m) else str(c["m_OverrideClip"])
                print(f"    [{i}] orig={orig} -> {nm} ({c['m_OverrideClip']})")

# 3. Also inspect Mixmaster, Bludgeon, Windblade, Sideswipe S1/S2 PrefabList FX names to see what's in global character_fx vs local bundles
cfx_path = ROOT_BL / "extracted_apk" / "assets" / "assetpack" / "characters_procedural_odr"
print("\n=== Checking FX bundles in assets_netflix & extracted_apk ===")
for p in sorted((ROOT_BL / "assets_netflix").glob("*.assetbundle")):
    print(f"  netflix: {p.name}")
for p in sorted((ROOT_GM / "extracted_apk" / "assets" / "assetpack").glob("*fx*.assetbundle")):
    print(f"  tftf fx: {p.name}")
for p in sorted((ROOT_GM / "assets_netflix").glob("*fx*.assetbundle")):
    print(f"  tftf netflix fx: {p.name}")
