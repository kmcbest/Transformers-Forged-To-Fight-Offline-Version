#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recolor_breakdown_textures.py

Generates authentic G1 / Stunticon Breakdown (打击) textures:
1. cha_breakdown_gs_main_a.png (1024x1024)
   - Helmet: Deep metallic teal-blue (#16405C)
   - Faceplate: Vibrant orange-red (#E03818) with glowing ruby red eyes (#FF1820)
   - Body & Armor: Off-white / pearl white (#EEF1F5)
   - Lower legs & car flanks: Deep metallic teal-blue (#16405C)
   - Front hood: Orange-red trapezoid with centered purple Decepticon emblem
2. cha_breakdown_gs_tform_misc_a.png (512x512)
   - Car roof, fenders, spoiler: Off-white (#EEF1F5)
   - Rocker panels & side skirts: Deep metallic teal-blue (#16405C)
3. cha_breakdown_gs_wpns_a.png (1024x1024)
   - Rocket launcher & pistol: Deep metallic teal-blue and gunmetal gray
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

out_dir = Path("assets_redeco")
out_dir.mkdir(exist_ok=True)

# Load Sideswipe base textures
main_img = Image.open("scratch_sideswipe_textures/cha_sideswipe_gs_deluxe2008_main_a.png").convert("RGBA")
misc_img = Image.open("scratch_sideswipe_textures/tform_misc_A.png").convert("RGBA")
wpns_img = Image.open("scratch_sideswipe_textures/cha_sideswipe_gs_deluxe2008_wpns_a.png").convert("RGBA")

# Load clean Decepticon logo
def get_clean_decepticon_logo():
    logo_path = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\d633472c-6af9-4876-ba8e-7c2b6d54f933\decepticon_logo_clean_1789196964736.jpg")
    img = Image.open(logo_path).convert("RGBA")
    arr = np.array(img).astype(float)
    green = arr[:, :, 1] / 255.0
    alpha = np.clip((0.85 - green) / 0.25, 0.0, 1.0) * 255.0
    res_arr = np.zeros_like(arr, dtype=np.uint8)
    res_arr[:, :, 0] = 110
    res_arr[:, :, 1] = 20
    res_arr[:, :, 2] = 160
    res_arr[:, :, 3] = alpha.astype(np.uint8)
    non_empty = np.argwhere(res_arr[:, :, 3] > 10)
    ymin, xmin = non_empty.min(axis=0)
    ymax, xmax = non_empty.max(axis=0)
    return Image.fromarray(res_arr).crop((xmin, ymin, xmax + 1, ymax + 1))

dec_logo = get_clean_decepticon_logo()

# =========================================================================
# 1. Recolor Main Texture (1024x1024)
# =========================================================================
m_arr = np.array(main_img).copy()
r_m = m_arr[:, :, 0].astype(float) / 255.0
g_m = m_arr[:, :, 1].astype(float) / 255.0
b_m = m_arr[:, :, 2].astype(float) / 255.0
lum_m = 0.299 * r_m + 0.587 * g_m + 0.114 * b_m

mx_m = np.maximum(np.maximum(r_m, g_m), b_m)
mn_m = np.minimum(np.minimum(r_m, g_m), b_m)
df_m = mx_m - mn_m
sat_m = np.zeros_like(mx_m)
nz_m = mx_m > 1e-5
sat_m[nz_m] = df_m[nz_m] / mx_m[nz_m]

# Sideswipe red paint mask (high saturation, high R, low G and B)
is_red_paint = (r_m > 0.45) & (g_m < 0.35) & (b_m < 0.35) & (r_m > g_m + 0.20)

# Sideswipe black helmet dome: x in [0, 320], y in [0, 270], low lum, low sat
is_helmet = np.zeros_like(is_red_paint)
is_helmet[:270, :320] = (lum_m[:270, :320] < 0.40) & (sat_m[:270, :320] < 0.30)

# Faceplate: x in [300, 480], y in [0, 140]
is_face = np.zeros_like(is_red_paint)
is_face[:140, 300:480] = (lum_m[:140, 300:480] > 0.25) & (sat_m[:140, 300:480] < 0.35)

# Eyes: inside face area, blue in Sideswipe (high B)
is_eyes = np.zeros_like(is_red_paint)
is_eyes[:140, 300:480] = (b_m[:140, 300:480] > r_m[:140, 300:480] + 0.15) & (b_m[:140, 300:480] > 0.35)
# Dilate eyes slightly
e_img = Image.fromarray(is_eyes.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(size=3))
is_eyes = np.array(e_img) > 0

# Lower legs & car flanks: x in [650, 1024], y in [220, 1024]
is_legs_flanks = np.zeros_like(is_red_paint)
is_legs_flanks[220:, 650:] = is_red_paint[220:, 650:]

# Front hood: x in [0, 340], y in [530, 900]
is_hood = np.zeros_like(is_red_paint)
is_hood[530:900, :340] = is_red_paint[530:900, :340]

# All other red panels (chest, shoulders, thighs, arms):
is_other_red = is_red_paint & (~is_legs_flanks) & (~is_hood)

# Target Colors:
# A. Off-White / Pearl White (#F0F2F5):
# Modulate with original brightness/shading
white_r = np.clip(lum_m * 180 + 60, 0, 255).astype(np.uint8)
white_g = np.clip(lum_m * 182 + 62, 0, 255).astype(np.uint8)
white_b = np.clip(lum_m * 188 + 65, 0, 255).astype(np.uint8)

# B. Deep Metallic Teal-Blue (#16405C):
# R: ~22, G: ~64, B: ~92
teal_r = np.clip(lum_m * 50 + 10, 0, 255).astype(np.uint8)
teal_g = np.clip(lum_m * 110 + 25, 0, 255).astype(np.uint8)
teal_b = np.clip(lum_m * 145 + 40, 0, 255).astype(np.uint8)

# C. Helmet: Deep Metallic Teal-Blue
m_arr[is_helmet, 0] = teal_r[is_helmet]
m_arr[is_helmet, 1] = teal_g[is_helmet]
m_arr[is_helmet, 2] = teal_b[is_helmet]

# D. Faceplate: Vibrant Orange-Red (#E03818)
face_r = np.clip(lum_m * 190 + 50, 0, 255).astype(np.uint8)
face_g = np.clip(lum_m * 60 + 10, 0, 255).astype(np.uint8)
face_b = np.clip(lum_m * 30 + 5, 0, 255).astype(np.uint8)
m_arr[is_face, 0] = face_r[is_face]
m_arr[is_face, 1] = face_g[is_face]
m_arr[is_face, 2] = face_b[is_face]

# E. Eyes: Glowing Ruby Red (#FF1820)
m_arr[is_eyes, 0] = 255
m_arr[is_eyes, 1] = 25
m_arr[is_eyes, 2] = 30

# F. Lower legs & outer door flanks: Deep Metallic Teal-Blue
m_arr[is_legs_flanks, 0] = teal_r[is_legs_flanks]
m_arr[is_legs_flanks, 1] = teal_g[is_legs_flanks]
m_arr[is_legs_flanks, 2] = teal_b[is_legs_flanks]

# G. Other body panels: Off-white
m_arr[is_other_red, 0] = white_r[is_other_red]
m_arr[is_other_red, 1] = white_g[is_other_red]
m_arr[is_other_red, 2] = white_b[is_other_red]

# H. Front hood: Turn base to Off-white first
m_arr[is_hood, 0] = white_r[is_hood]
m_arr[is_hood, 1] = white_g[is_hood]
m_arr[is_hood, 2] = white_b[is_hood]

# Convert to PIL for graphic decal work
res_main = Image.fromarray(m_arr)
draw_m = ImageDraw.Draw(res_main)

# I. Front Hood Decal: Classic Orange-Red Trapezoid (Mirrored in 3D across x=0)
# The hood centerline is at x = 0.
# Draw half-trapezoid from x = 0 to x = 115..145
hood_poly = [
    (0, 560),
    (110, 560),
    (140, 860),
    (0, 860),
]
draw_m.polygon(hood_poly, fill=(235, 60, 30, 255), outline=(190, 35, 15, 255))

# Half Decepticon insignia touching x = 0 (right half of logo)
W_logo, H_logo = dec_logo.size
right_half_logo = dec_logo.crop((W_logo // 2, 0, W_logo, H_logo))
target_w = 70
target_h = int(right_half_logo.height * (target_w / right_half_logo.width))
half_logo_resized = right_half_logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
paste_y = (560 + 860 - target_h) // 2
res_main.paste(half_logo_resized, (0, paste_y), half_logo_resized)

res_main.save(out_dir / "cha_breakdown_gs_main_a.png")
print("[+] Saved assets_redeco/cha_breakdown_gs_main_a.png!")

# =========================================================================
# 2. Recolor Misc Texture (512x512)
# =========================================================================
c_arr = np.array(misc_img).copy()
r_c = c_arr[:, :, 0].astype(float) / 255.0
g_c = c_arr[:, :, 1].astype(float) / 255.0
b_c = c_arr[:, :, 2].astype(float) / 255.0
lum_c = 0.299 * r_c + 0.587 * g_c + 0.114 * b_c

is_red_misc = (r_c > 0.45) & (g_c < 0.35) & (b_c < 0.35) & (r_c > g_c + 0.20)

# Rocker panels & side skirts: x in [0, 256], y in [130, 256]
is_skirt = np.zeros_like(is_red_misc)
is_skirt[130:256, :256] = is_red_misc[130:256, :256]

# Other car body panels (roof, rear wing, fenders):
is_body_misc = is_red_misc & (~is_skirt)

white_c_r = np.clip(lum_c * 180 + 60, 0, 255).astype(np.uint8)
white_c_g = np.clip(lum_c * 182 + 62, 0, 255).astype(np.uint8)
white_c_b = np.clip(lum_c * 188 + 65, 0, 255).astype(np.uint8)

teal_c_r = np.clip(lum_c * 50 + 10, 0, 255).astype(np.uint8)
teal_c_g = np.clip(lum_c * 110 + 25, 0, 255).astype(np.uint8)
teal_c_b = np.clip(lum_c * 145 + 40, 0, 255).astype(np.uint8)

c_arr[is_body_misc, 0] = white_c_r[is_body_misc]
c_arr[is_body_misc, 1] = white_c_g[is_body_misc]
c_arr[is_body_misc, 2] = white_c_b[is_body_misc]

c_arr[is_skirt, 0] = teal_c_r[is_skirt]
c_arr[is_skirt, 1] = teal_c_g[is_skirt]
c_arr[is_skirt, 2] = teal_c_b[is_skirt]

res_misc = Image.fromarray(c_arr)
res_misc.save(out_dir / "cha_breakdown_gs_tform_misc_a.png")
print("[+] Saved assets_redeco/cha_breakdown_gs_tform_misc_a.png!")

# =========================================================================
# 3. Recolor Weapons (1024x1024)
# =========================================================================
w_arr = np.array(wpns_img).copy()
lum_w = (0.299 * w_arr[:, :, 0] + 0.587 * w_arr[:, :, 1] + 0.114 * w_arr[:, :, 2]) / 255.0

# In Sideswipe, weapons have red and silver parts.
# In Breakdown, make weapons Deep Metallic Teal-Blue with gunmetal accents
w_teal_r = np.clip(lum_w * 45 + 15, 0, 255).astype(np.uint8)
w_teal_g = np.clip(lum_w * 85 + 30, 0, 255).astype(np.uint8)
w_teal_b = np.clip(lum_w * 120 + 45, 0, 255).astype(np.uint8)

w_arr[:, :, 0] = w_teal_r
w_arr[:, :, 1] = w_teal_g
w_arr[:, :, 2] = w_teal_b

res_wpns = Image.fromarray(w_arr)
res_wpns.save(out_dir / "cha_breakdown_gs_wpns_a.png")
print("[+] Saved assets_redeco/cha_breakdown_gs_wpns_a.png!")
