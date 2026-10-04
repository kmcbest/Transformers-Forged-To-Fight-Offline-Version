# -*- coding: utf-8 -*-
"""
patch_textures_and_materials_only.py

SURGICAL PATCH SCRIPT:
ONLY modifies textures and material properties in assets_redeco/elita_one_gs.assetbundle.
STRICTLY NEVER TOUCHES ANY MESH, BINDPOSE, BONE, OR SMR!
"""
import sys
from pathlib import Path
from PIL import Image
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
BUNDLE_PATH = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
TEX_DIR = ROOT / "tools" / "elita_one" / "processed_textures"

MAIN_DIFFUSE_PATH = TEX_DIR / "elita_main_diffuse.png"
MAIN_RAOE_PATH = TEX_DIR / "elita_main_raoe.png"
VEH_RAOE_PATH = TEX_DIR / "elita_veh_atlas_raoe.png"

for p in [BUNDLE_PATH, MAIN_DIFFUSE_PATH, MAIN_RAOE_PATH, VEH_RAOE_PATH]:
    if not p.is_file():
        raise FileNotFoundError(f"Missing {p}")

print(f"[*] Loading bundle: {BUNDLE_PATH}...")
env = UnityPy.load(str(BUNDLE_PATH))

textures_updated = 0
materials_updated = 0

for obj in env.objects:
    # 1. ONLY update Textures
    if obj.type.name == "Texture2D":
        data = obj.read()
        if data.m_Name == "cha_arcee_gs_deluxe2014_main_a":
            img = Image.open(MAIN_DIFFUSE_PATH).convert("RGBA")
            data.image = img
            data.save()
            textures_updated += 1
            print(f"[✓] Updated Texture2D Diffuse: {data.m_Name} ({img.size[0]}x{img.size[1]})")
        elif data.m_Name == "main_tform_misc_RAOE":
            img = Image.open(MAIN_RAOE_PATH).convert("RGB")
            data.image = img
            data.save()
            textures_updated += 1
            print(f"[✓] Updated Texture2D RAOE: {data.m_Name} ({img.size[0]}x{img.size[1]})")
        elif data.m_Name == "wpns_RAOE":
            img = Image.open(VEH_RAOE_PATH).convert("RGB")
            data.image = img
            data.save()
            textures_updated += 1
            print(f"[✓] Updated Texture2D RAOE: {data.m_Name} ({img.size[0]}x{img.size[1]})")

    # 2. ONLY update target Materials
    elif obj.type.name == "Material" and obj.path_id in [-737396187749761411, 5182645448333425879, 6920099848281342549]:
        mat = obj.read_typetree()
        saved_props = mat.get("m_SavedProperties", {})

        new_floats = []
        for k, v in saved_props.get("m_Floats", []):
            if k == "_Mode":
                new_floats.append((k, 3.0))  # Clearcoat mode, strictly matching official Kabam PBR
            elif k == "_metallic_range":
                new_floats.append((k, 0.45))
            elif k == "_roughness_range":
                new_floats.append((k, 0.35))
            elif k == "_emissive_range":
                new_floats.append((k, 0.0))  # Must be 0.0! In Character/PBR, 0.0 means 0 cutoff threshold. 1.0 kills emission!
            elif k == "_emissive_overbright_range":
                new_floats.append((k, 120.0))  # Match Arcee and Optimus HDR bloom factor
            elif k == "_emissive_pulse_intensity_range":
                new_floats.append((k, 0.10))
            elif k == "_emissive_pulse_time_range":
                new_floats.append((k, 1.5))
            elif k == "_emissive_ramp_range":
                new_floats.append((k, 0.70))
            elif k == "_emissive_none":
                new_floats.append((k, 0.0))
            else:
                new_floats.append((k, v))
        saved_props["m_Floats"] = new_floats

        new_colors = []
        for k, v in saved_props.get("m_Colors", []):
            if k in ["_base_col", "_Color", "_base2_col"]:
                new_colors.append((k, {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}))
            elif k == "_emissive_intensity_col":
                # Electric cyan: R=0.04, G=0.75, B=1.0, Alpha=0.0 strictly matching official character conventions
                new_colors.append((k, {'r': 0.04, 'g': 0.75, 'b': 1.0, 'a': 0.0}))
            else:
                new_colors.append((k, v))
        saved_props["m_Colors"] = new_colors


        obj.save_typetree(mat)
        materials_updated += 1
        print(f"[✓] Updated Material {obj.path_id}: {mat.get('m_Name')} (_roughness=0.35, _emissive=120.0, _col=[0.8, 0.95, 1.0])")

print(f"\n[*] Saving bundle with packer='lz4' (Textures: {textures_updated}, Materials: {materials_updated})...")
bf = list(env.files.values())[0]
with open(BUNDLE_PATH, "wb") as f:
    f.write(bf.save(packer="lz4"))

size_mb = BUNDLE_PATH.stat().st_size / (1024 * 1024)
print(f"[✓] SUCCESS: Bundle saved! Size: {size_mb:.2f} MB")
