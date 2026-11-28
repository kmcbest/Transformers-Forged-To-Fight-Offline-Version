import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path
from PIL import Image
import numpy as np
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_TEX = ROOT / "3rd-party-models" / "WildRider" / "02_textures"
UNITY_WR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "WildRider"
UNITY_TEX = UNITY_WR / "Textures"
UNITY_PROWL = UNITY_WR / "Prowl"
UNITY_TEX.mkdir(parents=True, exist_ok=True)
UNITY_PROWL.mkdir(parents=True, exist_ok=True)

# 1. Copy Diffuse & Normal_unity, plus generate Emission.png for Unity Standard shader
for fn in ["cha_wildrider_main_Diffuse.png", "cha_wildrider_main_Normal_unity.png", "cha_wildrider_main_RAOE.png"]:
    shutil.copy2(WR_TEX / fn, UNITY_TEX / fn)

diff_arr = np.array(Image.open(WR_TEX / "cha_wildrider_main_Diffuse.png").convert("RGB"), dtype=np.float32)
raoe_arr = np.array(Image.open(WR_TEX / "cha_wildrider_main_RAOE.png").convert("RGB"), dtype=np.float32)
emis_mask = raoe_arr[:, :, 2:3] / 255.0
emis_rgb = np.clip(diff_arr * emis_mask, 0, 255).astype(np.uint8)
Image.fromarray(emis_rgb, mode="RGB").save(UNITY_TEX / "cha_wildrider_main_Emission.png")
print(f"[✓] Copied WildRider textures & generated cha_wildrider_main_Emission.png to {UNITY_TEX}")

# 2. Extract Prowl reference textures + check Fight AOC clip names + shotgun SMR bone
prowl_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(prowl_bundle))
gos = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "GameObject"}
trs = {o.path_id: o.read_typetree() for o in env.objects if o.type.name == "Transform"}

for o in env.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        if t.m_Name in ("cha_prowl_gs_deluxe2016_main_a", "tform_misc_A", "cha_prowl_gs_deluxe2016_wpns_a"):
            t.image.convert("RGBA").save(UNITY_PROWL / f"{t.m_Name}.png")
            print(f"  Extracted Prowl texture: {t.m_Name}.png")
    elif o.path_id == -8799352062880271755 and o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print("\n=== Prowl Fight AOC Clip Slots (first 40 non-empty) ===")
        for i, c in enumerate(tt.get("m_Clips", [])):
            orig = c.get("m_OriginalClip", {})
            ovr = c.get("m_OverrideClip", {})
            if ovr.get("m_PathID", 0) != 0:
                print(f"  [{i:2d}] orig=({orig.get('m_FileID')},{orig.get('m_PathID')}) ovr=({ovr.get('m_FileID')},{ovr.get('m_PathID')})")
    elif o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        if tt.get("m_Mesh", {}).get("m_PathID") == -7947891575776091319:
            b_pids = [b.get("m_PathID") for b in tt.get("m_Bones", [])]
            b_names = [gos.get(trs.get(bp,{}).get("m_GameObject",{}).get("m_PathID"),{}).get("m_Name") for bp in b_pids]
            print(f"\nShotgun SMR PID={o.path_id}: bones={b_names}")
            break
