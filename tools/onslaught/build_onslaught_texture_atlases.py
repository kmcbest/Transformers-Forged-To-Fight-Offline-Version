import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path
from PIL import Image, ImageEnhance
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_TEX = ROOT / "3rd-party-models" / "onslaught" / "textures"
OUT_DIR = ROOT / "3rd-party-models" / "onslaught" / "processed_textures"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Onslaught"
OUT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR.mkdir(parents=True, exist_ok=True)


def enhance_diffuse(rgba_img, gamma=0.82, gain=1.16, sat=1.18, contrast=1.08):
    arr = np.array(rgba_img, dtype=np.float32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3].astype(np.uint8)
    rgb_lifted = np.clip(255.0 * ((rgb / 255.0) ** gamma) * gain, 0, 255).astype(np.uint8)
    pil_rgb = Image.fromarray(rgb_lifted, mode="RGB")
    pil_rgb = ImageEnhance.Color(pil_rgb).enhance(sat)
    pil_rgb = ImageEnhance.Contrast(pil_rgb).enhance(contrast)
    return Image.fromarray(np.dstack((np.array(pil_rgb), alpha)), mode="RGBA")


print("=== 1. BUILDING ONSLAUGHT ROBOT + WEAPON 2048x2048 ATLASES ===")
ATLAS_W, ATLAS_H = 2048, 2048

diffuse_atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (55, 58, 64, 255))
normal_atlas = Image.new("RGB", (ATLAS_W, ATLAS_H), (128, 128, 255))
emission_color_atlas = Image.new("RGB", (ATLAS_W, ATLAS_H), (0, 0, 0))
raoe_atlas = Image.new("RGB", (ATLAS_W, ATLAS_H), (135, 215, 0))  # R=135 satin roughness, G=215 bright AO, B=0 emission

ATLAS_SLOTS = {
    "legs": {
        "box": (0, 1024, 1024, 2048),
        "size": (1024, 1024),
        "diffuse": "rb_onslaught_legs_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_legs_cust_n.jpg",
        "emission": "rb_onslaught_legs_cust_e.jpg",
    },
    "chest": {
        "box": (0, 0, 1024, 1024),
        "size": (1024, 1024),
        "diffuse": "rb_onslaught_chest_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_chest_cust_n.jpg",
        "emission": "rb_onslaught_chest_cust_e.jpg",
    },
    "head": {
        "box": (1024, 1536, 1536, 2048),
        "size": (512, 512),
        "diffuse": "rb_onslaught_head_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_head_cust_n.jpg",
        "emission": "rb_onslaught_head_cust_e.jpg",
    },
    "armlo": {
        "box": (1536, 1536, 2048, 2048),
        "size": (512, 512),
        "diffuse": "rb_onslaught_armlo_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_armlo_cust_n.jpg",
        "emission": "rb_onslaught_armlo_cust_e.jpg",
    },
    "armup": {
        "box": (1024, 1024, 1536, 1536),
        "size": (512, 512),
        "diffuse": "rb_onslaught_armup_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_armup_cust_n.jpg",
        "emission": None,
    },
    "wheel": {
        "box": (1536, 1024, 2048, 1536),
        "size": (512, 512),
        "diffuse": "rb_onslaught_wheel_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_wheel_cust_n.jpg",
        "emission": "rb_onslaught_wheel_cust_e.jpg",
    },
    "rocketlauncher": {
        "box": (1024, 512, 1536, 1024),
        "size": (512, 512),
        "diffuse": "wep_rocketlauncher_matinst.jpg",
        "normal": "wep_rocketlauncher_n.jpg",
        "emission": "wep_rocketlauncher_e.jpg",
    },
    "heavymg": {
        "box": (1536, 512, 2048, 1024),
        "size": (512, 512),
        "diffuse": "wep_heavymg_matinst.jpg",
        "normal": "wep_heavymg_matinst_n.jpg",
        "emission": "wep_heavymg_matinst_e.jpg",
    },
    "joint": {
        "box": (1024, 0, 1536, 512),
        "size": (512, 512),
        "diffuse": "rb_armup_cust_matinst_inst.jpg",
        "normal": "rb_armup_cust_matinst_n.jpg",
        "emission": None,
    },
    "logo": {
        "box": (1536, 0, 2048, 512),
        "size": (512, 512),
        "diffuse": "DecepticonLogo.png",
        "bg_color": (104, 108, 112, 255),  # Matches brushed steel chest badge plate
        "normal": None,
        "emission": None,
    },
}

for part_name, info in ATLAS_SLOTS.items():
    box = info["box"]
    target_size = info["size"]

    if info.get("diffuse"):
        d_file = SRC_TEX / info["diffuse"]
        if d_file.exists():
            d_img = Image.open(d_file).convert("RGBA").resize(target_size, Image.Resampling.LANCZOS)
            if "bg_color" in info:
                bg = Image.new("RGBA", target_size, info["bg_color"])
                bg.alpha_composite(d_img)
                diffuse_atlas.paste(bg, (box[0], box[1]))
            else:
                d_enh = enhance_diffuse(d_img)
                diffuse_atlas.paste(d_enh, (box[0], box[1]))

    if info.get("normal"):
        n_file = SRC_TEX / info["normal"]
        if n_file.exists():
            n_img = Image.open(n_file).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
            normal_atlas.paste(n_img, (box[0], box[1]))

    if info.get("emission"):
        e_file = SRC_TEX / info["emission"]
        if e_file.exists():
            e_rgb = Image.open(e_file).convert("RGB").resize(target_size, Image.Resampling.BILINEAR)
            emission_color_atlas.paste(e_rgb, (box[0], box[1]))
            e_lum = np.array(e_rgb.convert("L"), dtype=np.float32)
            sub_raoe = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
            sub_raoe[:, :, 0] = 135
            sub_raoe[:, :, 1] = 215
            sub_raoe[:, :, 2] = np.clip(e_lum * 1.45, 0, 255).astype(np.uint8)
            raoe_atlas.paste(Image.fromarray(sub_raoe), (box[0], box[1]))

# Bake subtle self-illumination into diffuse so glow strips & yellow visor pop even without bloom
diff_arr = np.array(diffuse_atlas, dtype=np.float32)
em_arr = np.array(emission_color_atlas, dtype=np.float32)
diff_arr[:, :, :3] = np.clip(diff_arr[:, :, :3] + em_arr * 0.65, 0, 255)
diffuse_final = Image.fromarray(diff_arr.astype(np.uint8), mode="RGBA")

# Normal maps:
# 1) Unity Standard shader normal map (OpenGL Y-inverted, Z=255)
norm_unity_arr = np.array(normal_atlas, dtype=np.uint8)
norm_unity_arr[:, :, 1] = 255 - norm_unity_arr[:, :, 1]
# 2) Kabam PBR shader normal map (NM.Blue encodes metallic; keep ~140 satin metallic so armor isn't black mirror)
norm_kabam_arr = norm_unity_arr.copy()
norm_kabam_arr[:, :, 2] = 140

diffuse_final.save(OUT_DIR / "cha_onslaught_main_a.png")
Image.fromarray(norm_kabam_arr).save(OUT_DIR / "cha_onslaught_main_NM.png")
Image.fromarray(norm_unity_arr).save(OUT_DIR / "cha_onslaught_main_NM_unity.png")
raoe_atlas.save(OUT_DIR / "cha_onslaught_main_tform_misc_RAOE.png")
emission_color_atlas.save(OUT_DIR / "cha_onslaught_main_Emission.png")
print("[✓] Saved 2048x2048 Robot + Weapon Atlases (Diffuse, Kabam NM, Unity NM, RAOE, Emission)")


print("\n=== 2. BUILDING ONSLAUGHT VEHICLE 2048x2048 ATLASES (4 MATERIALS) ===")
# Layout:
# - vh_body:     PIL (0, 0, 1024, 1024)       -> UV U[0.0, 0.5], V[0.5, 1.0]
# - vh_interior: PIL (0, 1024, 1024, 2048)    -> UV U[0.0, 0.5], V[0.0, 0.5] (2x2 tiled 512x512 so wrapped UVs never bleed!)
# - wheel:       PIL (1024, 0, 2048, 1024)    -> UV U[0.5, 1.0], V[0.5, 1.0]
# - logo:        PIL (1024, 1024, 2048, 2048) -> UV U[0.5, 1.0], V[0.0, 0.5]
vh_diffuse = Image.new("RGBA", (2048, 2048), (55, 62, 74, 255))
vh_normal = Image.new("RGB", (2048, 2048), (128, 128, 255))
vh_emission = Image.new("RGB", (2048, 2048), (0, 0, 0))
vh_raoe = Image.new("RGB", (2048, 2048), (135, 215, 0))

# Slot A: vh_body (0, 0)
vb_d = enhance_diffuse(Image.open(SRC_TEX / "vh_onslaught_normspec_cust_e_mat_inst.jpg").convert("RGBA").resize((1024, 1024), Image.Resampling.LANCZOS))
vb_n = Image.open(SRC_TEX / "vh_onslaught_normspec_cust_n.jpg").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
vb_e = Image.open(SRC_TEX / "vh_onslaught_normspec_cust_e.jpg").convert("RGB").resize((1024, 1024), Image.Resampling.BILINEAR)
vh_diffuse.paste(vb_d, (0, 0))
vh_normal.paste(vb_n, (0, 0))
vh_emission.paste(vb_e, (0, 0))

# Slot B: vh_interior tiled 2x2 in (0, 1024, 1024, 2048)
vi_d = enhance_diffuse(Image.open(SRC_TEX / "vh_interior_mat.jpg").convert("RGBA").resize((512, 512), Image.Resampling.LANCZOS))
vi_n = Image.open(SRC_TEX / "vh_interior_n.jpg").convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
for tx in (0, 512):
    for ty in (1024, 1536):
        vh_diffuse.paste(vi_d, (tx, ty))
        vh_normal.paste(vi_n, (tx, ty))

# Slot C: wheel in (1024, 0, 2048, 1024)
vw_d = enhance_diffuse(Image.open(SRC_TEX / "rb_onslaught_wheel_cust_e_mat_inst.jpg").convert("RGBA").resize((1024, 1024), Image.Resampling.LANCZOS))
vw_n = Image.open(SRC_TEX / "rb_onslaught_wheel_cust_n.jpg").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
vw_e = Image.open(SRC_TEX / "rb_onslaught_wheel_cust_e.jpg").convert("RGB").resize((1024, 1024), Image.Resampling.BILINEAR)
vh_diffuse.paste(vw_d, (1024, 0))
vh_normal.paste(vw_n, (1024, 0))
vh_emission.paste(vw_e, (1024, 0))

# Slot D: logo in (1024, 1024, 2048, 2048)
vl_bg = Image.new("RGBA", (1024, 1024), (72, 86, 112, 255))
vl_fg = Image.open(SRC_TEX / "DecepticonLogo.png").convert("RGBA").resize((1024, 1024), Image.Resampling.LANCZOS)
vl_bg.alpha_composite(vl_fg)
vh_diffuse.paste(vl_bg, (1024, 1024))

# Bake emission glow into vehicle diffuse & RAOE
vd_arr = np.array(vh_diffuse, dtype=np.float32)
ve_arr = np.array(vh_emission, dtype=np.float32)
vd_arr[:, :, :3] = np.clip(vd_arr[:, :, :3] + ve_arr * 0.65, 0, 255)
vh_diffuse_final = Image.fromarray(vd_arr.astype(np.uint8), mode="RGBA")

vr_arr = np.array(vh_raoe, dtype=np.uint8)
vr_arr[:, :, 2] = np.clip(np.array(vh_emission.convert("L"), dtype=np.float32) * 1.45, 0, 255).astype(np.uint8)
vh_raoe_final = Image.fromarray(vr_arr, mode="RGB")

vnorm_unity = np.array(vh_normal, dtype=np.uint8)
vnorm_unity[:, :, 1] = 255 - vnorm_unity[:, :, 1]
vnorm_kabam = vnorm_unity.copy()
vnorm_kabam[:, :, 2] = 140

vh_diffuse_final.save(OUT_DIR / "cha_onslaught_vh_a.png")
Image.fromarray(vnorm_kabam).save(OUT_DIR / "cha_onslaught_vh_NM.png")
Image.fromarray(vnorm_unity).save(OUT_DIR / "cha_onslaught_vh_NM_unity.png")
vh_raoe_final.save(OUT_DIR / "cha_onslaught_vh_tform_misc_RAOE.png")
vh_emission.save(OUT_DIR / "cha_onslaught_vh_Emission.png")
print("[✓] Saved 2048x2048 Vehicle Atlases (Diffuse, Kabam NM, Unity NM, RAOE, Emission)")

for fn in [
    "cha_onslaught_main_a.png",
    "cha_onslaught_main_NM.png",
    "cha_onslaught_main_NM_unity.png",
    "cha_onslaught_main_tform_misc_RAOE.png",
    "cha_onslaught_main_Emission.png",
    "cha_onslaught_vh_a.png",
    "cha_onslaught_vh_NM.png",
    "cha_onslaught_vh_NM_unity.png",
    "cha_onslaught_vh_tform_misc_RAOE.png",
    "cha_onslaught_vh_Emission.png",
]:
    shutil.copy2(OUT_DIR / fn, UNITY_DIR / fn)
print("[✓] Synced all 10 processed Onslaught textures to Unity Assets/Onslaught/")
