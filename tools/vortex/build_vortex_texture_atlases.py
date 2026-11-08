import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_TEX = ROOT / "3rd-party-models" / "vortex" / "textures"
OUT_DIR = ROOT / "3rd-party-models" / "vortex" / "processed_textures"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Vortex"

OUT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR.mkdir(parents=True, exist_ok=True)

def enhance_diffuse(rgba_img, gamma=0.88, gain=1.12, sat=1.15, contrast=1.06):
    arr = np.array(rgba_img, dtype=np.float32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3].astype(np.uint8) if arr.shape[2] == 4 else np.full((arr.shape[0], arr.shape[1]), 255, dtype=np.uint8)
    rgb_lifted = np.clip(255.0 * ((rgb / 255.0) ** gamma) * gain, 0, 255).astype(np.uint8)
    pil_rgb = Image.fromarray(rgb_lifted, mode="RGB")
    pil_rgb = ImageEnhance.Color(pil_rgb).enhance(sat)
    pil_rgb = ImageEnhance.Contrast(pil_rgb).enhance(contrast)
    return Image.fromarray(np.dstack((np.array(pil_rgb), alpha)), mode="RGBA")

print("=== 1. BUILDING VORTEX ROBOT 2048x2048 PBR ATLASES ===")
ATLAS_W, ATLAS_H = 2048, 2048

diffuse_atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (45, 48, 52, 255))
normal_atlas = Image.new("RGB", (ATLAS_W, ATLAS_H), (128, 128, 255))
emission_atlas = Image.new("RGB", (ATLAS_W, ATLAS_H), (0, 0, 0))

# Perfect non-overlapping grid layout:
# 2 large 1024x1024 slots on left half:
#   legs: (0, 0, 1024, 1024) [PIL] -> U:[0, 0.5], V:[0.5, 1.0]
#   chest: (0, 1024, 1024, 2048) [PIL] -> U:[0, 0.5], V:[0, 0.5]
# 8 medium 512x512 slots on right half:
#   backpack: (1024, 0, 1536, 512) -> U:[0.5, 0.75], V:[0.75, 1.0]
#   bladeaut: (1024, 512, 1536, 1024) -> U:[0.5, 0.75], V:[0.5, 0.75]
#   factionlogo: (1536, 0, 2048, 512) -> U:[0.75, 1.0], V:[0.75, 1.0]
#   armup: (1024, 1024, 1536, 1536) -> U:[0.5, 0.75], V:[0.25, 0.5]
#   head: (1024, 1536, 1536, 2048) -> U:[0.5, 0.75], V:[0.0, 0.25]
#   armlo: (1536, 1024, 2048, 1536) -> U:[0.75, 1.0], V:[0.25, 0.5]
#   weapon: (1536, 1536, 2048, 2048) -> U:[0.75, 1.0], V:[0.0, 0.25]
ATLAS_SLOTS = {
    "legs": {
        "box": (0, 0, 1024, 1024),
        "size": (1024, 1024),
        "diffuse": "rb_vortex_legs_mat.jpg",
        "normal": "rb_vortex_legs_n.jpg",
        "emission": None
    },
    "chest": {
        "box": (0, 1024, 1024, 2048),
        "size": (1024, 1024),
        "diffuse": "rb_vortex_chest_mat.jpg",
        "normal": "rb_vortex_chest_n.jpg",
        "emission": None
    },
    "backpack": {
        "box": (1024, 0, 1536, 512),
        "size": (512, 512),
        "diffuse": "rb_vortex_backpack_mat.jpg",
        "normal": "rb_vortex_backpack_n.jpg",
        "emission": None
    },
    "bladeaut": {
        "box": (1024, 512, 1536, 1024),
        "size": (512, 512),
        "diffuse": "wep_bladeaut_mat.jpg",
        "normal": None,
        "emission": "wep_bladeaut_mat.jpg" # Glowing energon blade ribbon!
    },
    "factionlogo": {
        "box": (1536, 0, 2048, 512),
        "size": (512, 512),
        "diffuse": "DecepticonLogo.png",
        "normal": None,
        "emission": "DecepticonLogo.png" # Glowing purple Decepticon chest insignia!
    },
    "armup": {
        "box": (1024, 1024, 1536, 1536),
        "size": (512, 512),
        "diffuse": "rb_vortex_armup_mat.jpg",
        "normal": "rb_vortex_armup_n.jpg",
        "emission": None
    },
    "armlo": {
        "box": (1536, 1024, 2048, 1536),
        "size": (512, 512),
        "diffuse": "rb_vortex_armlo_mat.jpg",
        "normal": "rb_vortex_armlo_n.jpg",
        "emission": None
    },
    "head": {
        "box": (1024, 1536, 1536, 2048),
        "size": (512, 512),
        "diffuse": "rb_vortex_head_mat.jpg",
        "normal": "rb_vortex_head_n.jpg",
        "emission": None
    },
    "weapon": {
        "box": (1536, 1536, 2048, 2048),
        "size": (512, 512),
        "diffuse": "wep.jpg",
        "normal": None,
        "emission": "wep_e.jpg"
    }
}

for part, info in ATLAS_SLOTS.items():
    box = info["box"]
    target_size = info["size"]
    
    # Diffuse
    if info.get("diffuse"):
        df = SRC_TEX / info["diffuse"]
        if df.exists():
            dimg = Image.open(df).convert("RGBA").resize(target_size, Image.Resampling.LANCZOS)
            dimg = enhance_diffuse(dimg)
            diffuse_atlas.paste(dimg, box, dimg)
            print(f"  Pasted diffuse: {part:12s} ({info['diffuse']}) -> {box}")
    
    # Normal
    if info.get("normal"):
        nf = SRC_TEX / info["normal"]
        if nf.exists():
            nimg = Image.open(nf).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
            normal_atlas.paste(nimg, box)
            print(f"  Pasted normal:  {part:12s} ({info['normal']}) -> {box}")
    else:
        flat_norm = Image.new("RGB", target_size, (128, 128, 255))
        normal_atlas.paste(flat_norm, box)
        
    # Emission
    if info.get("emission"):
        ef = SRC_TEX / info["emission"]
        if ef.exists():
            eimg = Image.open(ef).convert("RGBA").resize(target_size, Image.Resampling.LANCZOS)
            earr = np.array(eimg)
            if part == "factionlogo":
                # Decepticon logo: make alpha mask glow intense purple (180, 50, 255)
                mask = earr[:, :, 3] > 30
                purple_glow = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
                purple_glow[mask] = [210, 65, 255]
                epil = Image.fromarray(purple_glow, mode="RGB").filter(ImageFilter.GaussianBlur(1.0))
                emission_atlas.paste(epil, box)
            elif part == "bladeaut":
                # Blade ribbon: purple glow
                rgb = earr[:, :, :3]
                mask = rgb.max(axis=-1) > 40
                purple_glow = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
                purple_glow[mask] = [225, 75, 255]
                epil = Image.fromarray(purple_glow, mode="RGB").filter(ImageFilter.GaussianBlur(1.0))
                emission_atlas.paste(epil, box)
            else:
                e_rgb = eimg.convert("RGB")
                emission_atlas.paste(e_rgb, box)
            print(f"  Pasted emission:{part:12s} ({info['emission']}) -> {box}")

# Add glowing Eyes for Head (Vortex gold/yellow T-visor!)
# Head is placed in box: (1024, 1536, 1536, 2048)
head_d_f = SRC_TEX / "rb_vortex_head_mat.jpg"
if head_d_f.exists():
    h_img = Image.open(head_d_f).convert("RGB").resize((512, 512))
    h_arr = np.array(h_img)
    r, g, b = h_arr[:, :, 0], h_arr[:, :, 1], h_arr[:, :, 2]
    visor_mask = (r > 130) & (g > 100) & (b < 100)
    
    h_emis = np.zeros((512, 512, 3), dtype=np.uint8)
    h_emis[visor_mask] = [255, 215, 30] # High intensity neon gold glow!
    h_emis_pil = Image.fromarray(h_emis, mode="RGB").filter(ImageFilter.GaussianBlur(1.0))
    emission_atlas.paste(h_emis_pil, (1024, 1536), Image.fromarray((visor_mask.astype(np.uint8)*255), mode="L"))
    print("  [✓] Embedded glowing gold T-visor eyes in emission atlas!")

# Build RAOE Atlas (Roughness, AO, Metallic mask in Normal.B, Emission in RAOE.B)
diff_arr = np.array(diffuse_atlas)
emis_arr = np.array(emission_atlas)
norm_arr = np.array(normal_atlas)

emis_gray = (emis_arr[:, :, 0] * 0.299 + emis_arr[:, :, 1] * 0.587 + emis_arr[:, :, 2] * 0.114).astype(np.uint8)

raoe_r = np.full((ATLAS_H, ATLAS_W), 130, dtype=np.uint8) # Satin roughness
raoe_g = np.full((ATLAS_H, ATLAS_W), 215, dtype=np.uint8) # Bright ambient occlusion
raoe_b = np.clip(emis_gray.astype(np.float32) * 1.5, 0, 255).astype(np.uint8) # Emissive mask

raoe_atlas = Image.fromarray(np.dstack((raoe_r, raoe_g, raoe_b)), mode="RGB")

# Kabam Normal Map Packing:
# Normal.B stores metallic mask. Dielectric paint armor = B=35. Blade/Joint metal = B=75.
norm_r = norm_arr[:, :, 0]
norm_g = norm_arr[:, :, 1]
norm_b = np.full((ATLAS_H, ATLAS_W), 35, dtype=np.uint8)
# In blade quadrant, set metallic higher:
norm_b[1536:2048, 1536:2048] = 75
norm_b[512:1024, 1024:1536] = 75

normal_unity = Image.fromarray(np.dstack((norm_r, norm_g, norm_b)), mode="RGB")

# Save Robot Textures
diffuse_atlas.save(OUT_DIR / "cha_vortex_main_a.png", "PNG")
diffuse_atlas.save(UNITY_DIR / "cha_vortex_main_a.png", "PNG")
normal_atlas.save(OUT_DIR / "cha_vortex_main_NM.png", "PNG")
normal_atlas.save(UNITY_DIR / "cha_vortex_main_NM.png", "PNG")
normal_unity.save(OUT_DIR / "cha_vortex_main_NM_unity.png", "PNG")
normal_unity.save(UNITY_DIR / "cha_vortex_main_NM_unity.png", "PNG")
emission_atlas.save(OUT_DIR / "cha_vortex_main_Emission.png", "PNG")
emission_atlas.save(UNITY_DIR / "cha_vortex_main_Emission.png", "PNG")
raoe_atlas.save(OUT_DIR / "cha_vortex_main_tform_misc_RAOE.png", "PNG")
raoe_atlas.save(UNITY_DIR / "cha_vortex_main_tform_misc_RAOE.png", "PNG")
print("[✓] Saved Robot PBR Atlases!")

print("\n=== 2. BUILDING VORTEX VEHICLE PBR TEXTURES ===")
vh_d_f = SRC_TEX / "vh_vortexbase_mat.jpg"
vh_n_f = SRC_TEX / "vh_vortexbase_n.jpg"

vh_d = Image.open(vh_d_f).convert("RGBA")
vh_d = enhance_diffuse(vh_d)
vh_w, vh_h = vh_d.size

vh_n = Image.open(vh_n_f).convert("RGB") if vh_n_f.exists() else Image.new("RGB", (vh_w, vh_h), (128, 128, 255))
vh_n_arr = np.array(vh_n)
vh_norm_unity = Image.fromarray(np.dstack((vh_n_arr[:, :, 0], vh_n_arr[:, :, 1], np.full((vh_h, vh_w), 30, dtype=np.uint8))), mode="RGB")

vh_raoe = Image.fromarray(np.dstack((
    np.full((vh_h, vh_w), 125, dtype=np.uint8),
    np.full((vh_h, vh_w), 220, dtype=np.uint8),
    np.zeros((vh_h, vh_w), dtype=np.uint8)
)), mode="RGB")

vh_emis = Image.new("RGB", (vh_w, vh_h), (0, 0, 0))

# Save Vehicle Textures
vh_d.save(OUT_DIR / "cha_vortex_vh_a.png", "PNG")
vh_d.save(UNITY_DIR / "cha_vortex_vh_a.png", "PNG")
vh_n.save(OUT_DIR / "cha_vortex_vh_NM.png", "PNG")
vh_n.save(UNITY_DIR / "cha_vortex_vh_NM.png", "PNG")
vh_norm_unity.save(OUT_DIR / "cha_vortex_vh_NM_unity.png", "PNG")
vh_norm_unity.save(UNITY_DIR / "cha_vortex_vh_NM_unity.png", "PNG")
vh_emis.save(OUT_DIR / "cha_vortex_vh_Emission.png", "PNG")
vh_emis.save(UNITY_DIR / "cha_vortex_vh_Emission.png", "PNG")
vh_raoe.save(OUT_DIR / "cha_vortex_vh_tform_misc_RAOE.png", "PNG")
vh_raoe.save(UNITY_DIR / "cha_vortex_vh_tform_misc_RAOE.png", "PNG")
print("[✓] Saved Vehicle PBR Atlases!")

print("\n[SUCCESS] All Vortex PBR Atlases built and deployed to Unity project!")
