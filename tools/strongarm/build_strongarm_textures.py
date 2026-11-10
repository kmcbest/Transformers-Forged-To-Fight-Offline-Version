import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

tex_dir = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\textures")
vh_tex_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.png")
out_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm")
out_dir.mkdir(parents=True, exist_ok=True)
local_out_dir = Path(r"E:\Agent\TFTF-blender\tools\strongarm\textures")
local_out_dir.mkdir(parents=True, exist_ok=True)
scratch_dir = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")


def upscale_image(im: Image.Image, target_size: tuple) -> Image.Image:
    """Super-resolution upscale with Lanczos resampling and subtle unsharp masking."""
    up = im.resize(target_size, Image.Resampling.LANCZOS)
    return up.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))


def tune_kabam_albedo(im_rgba: Image.Image) -> Image.Image:
    """
    Calibrate bright RID2015 cartoon diffuse for Kabam Showcase lighting at _base_col=1.0:
    - Boost color saturation (+14%) so blue armor stays rich royal/cobalt instead of dull navy.
    - Lift deep shadow blues slightly so shoulder armor details read cleanly in dark rooms.
    - Soften pure 255 whites slightly to ~236 (matching Prowl's official white ceiling)
      so white panels stay crisp without highlight clipping.
    """
    rgb = im_rgba.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(1.14)
    arr = np.array(rgb, dtype=np.float32) / 255.0

    # Gentle shadow lift (exponent 0.92 on darks) + soft top ceiling 238/255 on whites
    lifted = np.power(np.clip(arr, 0.0, 1.0), 0.92)
    # Soft compression above 0.85 -> 0.935 max (238) preserving shading & panel contrast
    high = lifted > 0.85
    lifted[high] = 0.85 + (lifted[high] - 0.85) * (0.085 / 0.15)

    out = np.empty((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    out[:, :, :3] = np.clip(lifted * 255.0, 0, 255).astype(np.uint8)
    out[:, :, 3] = 255
    return Image.fromarray(out, mode="RGBA")


def compute_saturation(rgb_arr: np.ndarray) -> np.ndarray:
    cmax = rgb_arr.max(axis=2)
    cmin = rgb_arr.min(axis=2)
    sat = np.zeros_like(cmax)
    nz = cmax > 1e-3
    sat[nz] = (cmax[nz] - cmin[nz]) / cmax[nz]
    return sat


def generate_normal_components(diffuse_img: Image.Image, strength: float = 2.8):
    """Compute OpenGL tangent-space Normal R, G, B (nz) arrays from diffuse gradients."""
    gray = diffuse_img.convert('L')
    arr = np.array(gray, dtype=np.float32) / 255.0
    padded = np.pad(arr, 1, mode='edge')

    gx = (
        -padded[:-2, :-2] + padded[:-2, 2:]
        - 2 * padded[1:-1, :-2] + 2 * padded[1:-1, 2:]
        - padded[2:, :-2] + padded[2:, 2:]
    ) / 8.0

    gy = (
        -padded[:-2, :-2] - 2 * padded[:-2, 1:-1] - padded[:-2, 2:]
        + padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]
    ) / 8.0

    gx = gx * strength
    gy = -gy * strength
    gz = np.ones_like(gx)

    norm = np.sqrt(gx**2 + gy**2 + gz**2)
    norm[norm == 0] = 1.0
    r = ((gx / norm) * 0.5 + 0.5) * 255.0
    g = ((gy / norm) * 0.5 + 0.5) * 255.0
    b = ((gz / norm) * 0.5 + 0.5) * 255.0
    return r.astype(np.uint8), g.astype(np.uint8), b.astype(np.uint8)


# ==============================================================================
# 1. Build Robot Diffuse Atlas (2048 x 2048, alpha=255 opaque)
# ==============================================================================
print("=== [1/5] Building Robot Diffuse Atlas (2048x2048) ===")
atlas_size = 2048
robot_atlas = Image.new("RGBA", (atlas_size, atlas_size), (40, 42, 48, 255))

slot_defs = {
    "chest_MD": (0, 1024, 1024, 1024),        # PIL (0, 0)
    "face_maskOn_MD": (0, 0, 1024, 1024),     # PIL (0, 1024)
    "leg_MD": (1024, 1536, 512, 512),         # PIL (1024, 0)
    "hand_MD": (1024, 1024, 512, 512),        # PIL (1024, 512)
    "body_MD": (1024, 512, 512, 512),         # PIL (1024, 1024)
    "head_MD": (1024, 0, 512, 512),           # PIL (1024, 1536)
    "doorWing_MD": (1536, 1536, 512, 512),    # PIL (1536, 0)
    "blaster_MD": (1536, 1024, 512, 512),     # PIL (1536, 512)
}

for name, (x0, y0, w, h) in slot_defs.items():
    p = tex_dir / f"{name}.png"
    if p.exists():
        im = Image.open(p).convert("RGBA")
        up = upscale_image(im, (w, h))
        up_arr = np.array(up, dtype=np.uint8)
        up_arr[:, :, 3] = 255
        pil_y = atlas_size - (y0 + h)
        robot_atlas.paste(Image.fromarray(up_arr, mode="RGBA"), (x0, pil_y))
        print(f"  Pasted '{name}' at PIL ({x0}, {pil_y}) size ({w}x{h})")

# Calibrated Kabam albedo copy (preserves vibrant blues while keeping white unclipped at _base_col=1.0)
robot_atlas_kabam = tune_kabam_albedo(robot_atlas)
robot_atlas_kabam.save(out_dir / "cha_strongarm_main_a.png")
robot_atlas_kabam.save(local_out_dir / "cha_strongarm_main_a.png")

# ==============================================================================
# 2. Build Robot Normal Maps: Unity (_NM_unity.png) & Kabam (_NM.png)
# ==============================================================================
print("\n=== [2/5] Building Robot Normal Maps (NM.B=0 on Painted Blue/White Armor!) ===")
nx, ny, nz = generate_normal_components(robot_atlas_kabam, strength=2.8)
robot_nm_unity = Image.fromarray(np.stack([nx, ny, nz], axis=-1), mode='RGB')
robot_nm_unity.save(out_dir / "cha_strongarm_main_NM_unity.png")
robot_nm_unity.save(local_out_dir / "cha_strongarm_main_NM_unity.png")

raw_rgb = np.array(robot_atlas.convert('RGB'), dtype=np.float32)
sat_r = compute_saturation(raw_rgb / 255.0)
diff_gray = np.array(robot_atlas.convert('L'), dtype=np.float32)

# Dielectric car-shell paint (ALL saturated colored armor/blue/red/gold OR white/silver face) -> Metallic = 0
# ONLY neutral dark grey metal chassis/joints (sat < 0.22 and 28 <= lum <= 115) -> Metallic = 95
r_metallic = np.where((sat_r < 0.22) & (diff_gray >= 28.0) & (diff_gray <= 115.0), 95, 0).astype(np.uint8)
robot_nm_kabam = Image.fromarray(np.stack([nx, ny, r_metallic], axis=-1), mode='RGB')
robot_nm_kabam.save(out_dir / "cha_strongarm_main_NM.png")
robot_nm_kabam.save(local_out_dir / "cha_strongarm_main_NM.png")
print(f"  [✓] Robot NM.B Metallic mean={r_metallic.mean():.1f} (dielectric blues & whites strictly 0!)")

# ==============================================================================
# 3. Build Robot RAOE + Vehicle RAOE into Unified 3-Channel RGB (R=Rough, G=AO, B=Emis)
# ==============================================================================
print("\n=== [3/5] Building Unified Kabam RGB RAOE (Controlled Forearm & Eye Glow) ===")
r_ch, g_ch, b_ch = raw_rgb[:, :, 0], raw_rgb[:, :, 1], raw_rgb[:, :, 2]

# Roughness: glossy car armor ~85..135, dark joints ~175..200
r_rough = np.clip((0.34 + (1.0 - diff_gray / 255.0) * 0.42) * 255.0, 85, 200).astype(np.uint8)
r_ao = np.clip(diff_gray * 0.25 + 190.0, 180, 255).astype(np.uint8)

# EMISSION (0 strictly everywhere on armor; calibrated per-part intensities to prevent white blowout):
r_emis = np.zeros((atlas_size, atlas_size), dtype=np.uint8)

# Pure cyan optics & vents (exclude baby-blue lips where R > 85)
pure_cyan = (g_ch > 175) & (b_ch > 175) & (r_ch < 85)
r_emis[pure_cyan] = 45  # Crisp neon cyan accents (waist/wings/shin chevrons) without halo bleed!

# Eyes in head_MD (bottom-right quadrant of head_MD PIL x=[1024..1536], y=[1536..2048]) stay gleaming bright!
head_mask = np.zeros((atlas_size, atlas_size), dtype=bool)
head_mask[1536:2048, 1024:1536] = True
r_emis[head_mask & pure_cyan] = 120

# Forearm Red/Blue Lightbar ONLY inside hand_MD: keep ultra-low self-lit (8) so Red stays RED & Blue stays BLUE!
hand_roi = np.zeros((atlas_size, atlas_size), dtype=bool)
hand_roi[895:958, 1106:1454] = True
forearm_red = hand_roi & (r_ch > 180) & (g_ch < 70) & (b_ch < 70)
forearm_blue = hand_roi & (b_ch > 190) & (r_ch < 50)
r_emis[forearm_red | forearm_blue] = 8

r_emis_img = Image.fromarray(r_emis, mode='L').filter(ImageFilter.GaussianBlur(radius=0.6))
r_emis = np.array(r_emis_img)
r_emis[r_emis < 6] = 0

em_preview = (raw_rgb * (r_emis.astype(np.float32) / 255.0)[:, :, None]).astype(np.uint8)
Image.fromarray(em_preview, mode='RGB').save(out_dir / "cha_strongarm_main_Emission.png")

# ==============================================================================
# 4. Build Vehicle Diffuse, Normal (Unity + Kabam), & 512x512 Vehicle RAOE
# ==============================================================================
print("\n=== [4/5] Building Vehicle Diffuse, Normals & Vehicle RAOE ===")
vh_raw = Image.open(vh_tex_path).convert("RGBA")
vh_up = upscale_image(vh_raw, (2048, 2048))
vh_kabam = tune_kabam_albedo(vh_up)
vh_kabam.save(out_dir / "cha_strongarm_vh_a.png")
vh_kabam.save(local_out_dir / "cha_strongarm_vh_a.png")

vnx, vny, vnz = generate_normal_components(vh_kabam, strength=3.0)
Image.fromarray(np.stack([vnx, vny, vnz], axis=-1), mode='RGB').save(out_dir / "cha_strongarm_vh_NM_unity.png")
Image.fromarray(np.stack([vnx, vny, vnz], axis=-1), mode='RGB').save(local_out_dir / "cha_strongarm_vh_NM_unity.png")

vh_raw_rgb = np.array(vh_up.convert('RGB'), dtype=np.float32)
sat_v = compute_saturation(vh_raw_rgb / 255.0)
vh_gray = np.array(vh_up.convert('L'), dtype=np.float32)
v_metallic = np.where((sat_v < 0.22) & (vh_gray >= 28.0) & (vh_gray <= 115.0), 85, 0).astype(np.uint8)
v_metallic[1590:, 1630:] = 0  # Wheels rubber = non-metal
vh_nm_kabam = Image.fromarray(np.stack([vnx, vny, v_metallic], axis=-1), mode='RGB')
vh_nm_kabam.save(out_dir / "cha_strongarm_vh_NM.png")
vh_nm_kabam.save(local_out_dir / "cha_strongarm_vh_NM.png")
print(f"  [✓] Vehicle NM.B Metallic mean={v_metallic.mean():.1f} (dielectric blues & whites strictly 0!)")

# Build 512x512 Vehicle RAOE
vh_512 = Image.open(vh_tex_path).convert("RGB")
v512_rgb = np.array(vh_512, dtype=np.float32)
vr, vg, vb = v512_rgb[:, :, 0], v512_rgb[:, :, 1], v512_rgb[:, :, 2]
v512_gray = np.array(vh_512.convert('L'), dtype=np.float32)

v512_rough = np.where(v512_gray > 100.0, 75, 118).astype(np.uint8)
v512_rough[v512_gray < 25.0] = 40      # Windshield glossy glass
v512_rough[398:, 408:] = 220           # Matte black rubber tires
v512_ao = np.clip(v512_gray * 0.25 + 188.0, 180, 255).astype(np.uint8)

v512_emis = np.zeros((512, 512), dtype=np.uint8)
v_cyan = (vg > 175) & (vb > 175) & (vr < 85)
v512_emis[v_cyan] = 65  # Headlights, hood vents

# Roof police red & blue sirens: low 18 so red stays red & blue stays blue without white blowout
v_red_siren_box = np.zeros((512, 512), dtype=bool)
v_red_siren_box[325:412, 402:466] = True
v512_emis[v_red_siren_box & (vr > 160) & (vg < 80) & (vb < 80)] = 20

v_blue_siren_box = np.zeros((512, 512), dtype=bool)
v_blue_siren_box[325:412, 302:358] = True
v512_emis[v_blue_siren_box & v_cyan] = 20

v512_emis = np.array(Image.fromarray(v512_emis, mode='L').filter(ImageFilter.GaussianBlur(radius=0.6)))
v512_emis[v512_emis < 8] = 0

vh_raoe_512 = Image.fromarray(np.stack([v512_rough, v512_ao, v512_emis], axis=-1), mode='RGB')
vh_raoe_2048 = vh_raoe_512.resize((2048, 2048), Image.Resampling.BILINEAR)
vh_raoe_2048.save(out_dir / "cha_strongarm_vh_tform_misc_RAOE.png")
vh_raoe_2048.save(local_out_dir / "cha_strongarm_vh_tform_misc_RAOE.png")

vh_em_preview = (np.array(vh_kabam.convert('RGB'), dtype=np.float32) * (np.array(vh_raoe_2048)[:, :, 2].astype(np.float32) / 255.0)[:, :, None]).astype(np.uint8)
Image.fromarray(vh_em_preview, mode='RGB').save(out_dir / "cha_strongarm_vh_Emission.png")

# ==============================================================================
# 5. Pack Unified main_tform_misc_RAOE
# ==============================================================================
print("\n=== [5/5] Packing Unified Robot+Vehicle RGB RAOE (OpenGL Bottom-Right Tile) ===")
unified_raoe = Image.fromarray(np.stack([r_rough, r_ao, r_emis], axis=-1), mode='RGB')
unified_raoe.paste(vh_raoe_512, (1536, 1536))
assert unified_raoe.mode == "RGB" and unified_raoe.size == (2048, 2048)

unified_raoe.save(out_dir / "cha_strongarm_main_tform_misc_RAOE.png")
unified_raoe.save(local_out_dir / "cha_strongarm_main_tform_misc_RAOE.png")

u_arr = np.array(unified_raoe)
print(f"  Unified RAOE stats:")
print(f"    R (Roughness): min={u_arr[:,:,0].min()}, max={u_arr[:,:,0].max()}, mean={u_arr[:,:,0].mean():.1f}")
print(f"    G (AO):        min={u_arr[:,:,1].min()}, max={u_arr[:,:,1].max()}, mean={u_arr[:,:,1].mean():.1f}")
print(f"    B (Emissive):  min={u_arr[:,:,2].min()}, max={u_arr[:,:,2].max()}, mean={u_arr[:,:,2].mean():.2f}, nonzero={(u_arr[:,:,2]>0).mean()*100:.2f}%")

Image.fromarray(u_arr[:, :, 2], mode='L').resize((1024, 1024), Image.Resampling.BILINEAR).save(scratch_dir / "verify_raoe_B_emissive_v2.png")
print("[SUCCESS] Rebuilt color-calibrated Kabam-compliant Strongarm PBR textures!")
