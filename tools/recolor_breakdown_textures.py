#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recolor_breakdown_textures.py

Generates authentic G1 / Stunticon Breakdown (打击) textures:
1. cha_breakdown_gs_main_a.png (1024x1024)
   - Helmet: Rich Royal Blue (#1D428A)
   - Faceplate: Vibrant orange-red (#E83818) with glowing ruby red eyes (#FF1820)
   - Chest / Torso: Radiant Pure White (#F8F9FA) with centered orange-red trapezoid and Decepticon emblem
   - Shoulders: Radiant Pure White (#F8F9FA)
   - Thighs & Pelvis: Rich Royal Blue (#1D428A)
   - Forearms: Rich Royal Blue (#1D428A)
   - Shins & Lower legs: Radiant Pure White (#F8F9FA)
2. cha_breakdown_gs_tform_misc_a.png (512x512)
   - Car roof, fenders, spoiler, doors: Radiant Pure White (#F8F9FA)
   - Shoulders: Radiant Pure White (#F8F9FA)
   - Thighs: Rich Royal Blue (#1D428A)
3. cha_breakdown_gs_wpns_a.png (1024x1024)
   - Rocket launcher & pistol: Rich Royal Blue & gunmetal gray
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import sys

out_dir = Path("assets_redeco")
out_dir.mkdir(exist_ok=True)

# Load base textures
main_base = Image.open("scratch_sideswipe_textures/cha_sideswipe_gs_deluxe2008_main_a.png").convert("RGBA")
misc_base = Image.open("scratch_sideswipe_textures/tform_misc_A.png").convert("RGBA")
wpns_base = Image.open("scratch_sideswipe_textures/cha_sideswipe_gs_deluxe2008_wpns_a.png").convert("RGBA")

# Load 3D mesh to accurately classify robot parts
sys.path.insert(0, ".")
from tools.analyze_submesh_bounds import d_verts, d_vts, sm0_tris, sm1_tris

# Load clean Decepticon logo
logo_path = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\d633472c-6af9-4876-ba8e-7c2b6d54f933\decepticon_logo_clean_1789196964736.jpg")
logo_raw = Image.open(logo_path).convert("RGBA")
l_arr = np.array(logo_raw).astype(float)
green = l_arr[:, :, 1] / 255.0
alpha = np.clip((0.85 - green) / 0.25, 0.0, 1.0) * 255.0
res_arr = np.zeros_like(l_arr, dtype=np.uint8)
res_arr[:, :, 0] = 130 # Decepticon Purple
res_arr[:, :, 1] = 20
res_arr[:, :, 2] = 190
res_arr[:, :, 3] = alpha.astype(np.uint8)
non_empty = np.argwhere(res_arr[:, :, 3] > 10)
ymin, xmin = non_empty.min(axis=0)
ymax, xmax = non_empty.max(axis=0)
dec_logo = Image.fromarray(res_arr).crop((xmin, ymin, xmax + 1, ymax + 1))

# Palette functions:
def make_white(lum):
    r = np.clip(lum * 55 + 200, 0, 255).astype(np.uint8)
    g = np.clip(lum * 55 + 200, 0, 255).astype(np.uint8)
    b = np.clip(lum * 53 + 205, 0, 255).astype(np.uint8)
    return r, g, b

def make_blue(lum):
    r = np.clip(lum * 35 + 15, 0, 255).astype(np.uint8)
    g = np.clip(lum * 55 + 40, 0, 255).astype(np.uint8)
    b = np.clip(lum * 75 + 165, 0, 255).astype(np.uint8)
    return r, g, b

def make_orange_red(lum):
    r = np.clip(lum * 170 + 75, 0, 255).astype(np.uint8)
    g = np.clip(lum * 45 + 15, 0, 255).astype(np.uint8)
    b = np.clip(lum * 20 + 10, 0, 255).astype(np.uint8)
    return r, g, b

def build_part_map(tris, W, H):
    part_img = Image.new("I", (W, H), 0)
    draw = ImageDraw.Draw(part_img)
    for vis, vtis in tris:
        cx = sum(d_verts[i][0] for i in vis) / 3.0
        cy = sum(d_verts[i][1] for i in vis) / 3.0
        cz = sum(d_verts[i][2] for i in vis) / 3.0
        pts = [(int(round(d_vts[vi][0] * W)), int(round((1.0 - d_vts[vi][1]) * H))) for vi in vtis]
        if cy > 8.0:
            pid = 2 if (cz > 0.18 and abs(cx) < 0.35) else 1 # 2: Faceplate, 1: Helmet
        elif 6.3 <= cy <= 8.2 and abs(cx) >= 0.75:
            pid = 3 # Shoulders -> Pure White!
        elif 5.2 <= cy <= 8.0 and abs(cx) < 0.75 and cz > -0.2:
            pid = 4 # Chest / Torso -> Pure White!
        elif (3.0 <= cy < 5.2 and abs(cx) < 1.1) or (4.8 <= cy < 5.3 and abs(cx) < 0.85):
            pid = 5 # Thighs / Pelvis -> Royal Blue!
        elif 3.8 <= cy < 6.3 and abs(cx) >= 1.15:
            pid = 6 # Forearms / Biceps -> Royal Blue!
        elif 0.8 <= cy < 3.0:
            pid = 7 # Shins -> Pure White!
        elif cy < 0.8:
            pid = 8 # Feet -> Blue/Dark
        else:
            pid = 9 # Car body / Roof / Doors -> Pure White!
        draw.polygon(pts, fill=pid)
    return np.array(part_img)

print("Building exact part maps for SM0 and SM1...")
p0_map = build_part_map(sm0_tris, 1024, 1024)
p1_map = build_part_map(sm1_tris, 512, 512)

# =========================================================================
# 1. SM0 (main_a): 1024x1024
# =========================================================================
m0_arr = np.array(main_base).copy()
r0 = m0_arr[:, :, 0].astype(float) / 255.0
g0 = m0_arr[:, :, 1].astype(float) / 255.0
b0 = m0_arr[:, :, 2].astype(float) / 255.0
lum0 = 0.299 * r0 + 0.587 * g0 + 0.114 * b0

is_eyes0 = np.zeros((1024, 1024), dtype=bool)
is_eyes0[:140, 300:480] = (b0[:140, 300:480] > r0[:140, 300:480] + 0.15) & (b0[:140, 300:480] > 0.35)
e_img = Image.fromarray(is_eyes0.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(size=3))
is_eyes0 = np.array(e_img) > 0

w0_r, w0_g, w0_b = make_white(lum0)
b0_r, b0_g, b0_b = make_blue(lum0)
f0_r, f0_g, f0_b = make_orange_red(lum0)

painted0 = lum0 > 0.10

# Blue parts on SM0 (Helmet, Thighs, Pelvis, Forearms, Feet):
blue_mask0 = painted0 & np.isin(p0_map, [1, 5, 6, 8]) & (p0_map != 3) & (p0_map != 4)
m0_arr[blue_mask0, 0] = b0_r[blue_mask0]
m0_arr[blue_mask0, 1] = b0_g[blue_mask0]
m0_arr[blue_mask0, 2] = b0_b[blue_mask0]

# White parts on SM0 (Shoulders, Chest/Torso, Shins, Car body):
white_mask0 = painted0 & (np.isin(p0_map, [3, 4, 7, 9]) | (p0_map == 0)) & (~blue_mask0)
m0_arr[white_mask0, 0] = w0_r[white_mask0]
m0_arr[white_mask0, 1] = w0_g[white_mask0]
m0_arr[white_mask0, 2] = w0_b[white_mask0]

# Faceplate on SM0:
face_mask0 = (p0_map == 2) & painted0
m0_arr[face_mask0, 0] = f0_r[face_mask0]
m0_arr[face_mask0, 1] = f0_g[face_mask0]
m0_arr[face_mask0, 2] = f0_b[face_mask0]

# Eyes on SM0:
m0_arr[is_eyes0, 0] = 255
m0_arr[is_eyes0, 1] = 25
m0_arr[is_eyes0, 2] = 30

# Front Hood Decal: Orange-Red Trapezoid + Decepticon logo
res_main = Image.fromarray(m0_arr)
draw_m = ImageDraw.Draw(res_main)

hood_poly = [
    (0, 560),
    (110, 560),
    (140, 860),
    (0, 860),
]
draw_m.polygon(hood_poly, fill=(235, 60, 30, 255), outline=(190, 35, 15, 255))

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
# 2. SM1 (tform_misc_A): 512x512
# =========================================================================
m1_arr = np.array(misc_base).copy()
r1 = m1_arr[:, :, 0].astype(float) / 255.0
g1 = m1_arr[:, :, 1].astype(float) / 255.0
b1 = m1_arr[:, :, 2].astype(float) / 255.0
lum1 = 0.299 * r1 + 0.587 * g1 + 0.114 * b1

w1_r, w1_g, w1_b = make_white(lum1)
b1_r, b1_g, b1_b = make_blue(lum1)

painted1 = lum1 > 0.10

# Blue parts on SM1 (Thighs, Forearms, Feet):
blue_mask1 = painted1 & np.isin(p1_map, [1, 5, 6, 8]) & (p1_map != 3) & (p1_map != 4)
m1_arr[blue_mask1, 0] = b1_r[blue_mask1]
m1_arr[blue_mask1, 1] = b1_g[blue_mask1]
m1_arr[blue_mask1, 2] = b1_b[blue_mask1]

# White parts on SM1 (Shoulders, Chest, Shins, Roof, Spoiler, Doors):
white_mask1 = painted1 & (np.isin(p1_map, [3, 4, 7, 9]) | (p1_map == 0)) & (~blue_mask1)
m1_arr[white_mask1, 0] = w1_r[white_mask1]
m1_arr[white_mask1, 1] = w1_g[white_mask1]
m1_arr[white_mask1, 2] = w1_b[white_mask1]

res_misc = Image.fromarray(m1_arr)
res_misc.save(out_dir / "cha_breakdown_gs_tform_misc_a.png")
print("[+] Saved assets_redeco/cha_breakdown_gs_tform_misc_a.png!")

# =========================================================================
# 3. SM2 (wpns_a): 1024x1024
# =========================================================================
w_arr = np.array(wpns_base).copy()
lum_w = (0.299 * w_arr[:, :, 0] + 0.587 * w_arr[:, :, 1] + 0.114 * w_arr[:, :, 2]) / 255.0
w_blue_r = np.clip(lum_w * 35 + 15, 0, 255).astype(np.uint8)
w_blue_g = np.clip(lum_w * 55 + 40, 0, 255).astype(np.uint8)
w_blue_b = np.clip(lum_w * 75 + 165, 0, 255).astype(np.uint8)

w_arr[:, :, 0] = w_blue_r
w_arr[:, :, 1] = w_blue_g
w_arr[:, :, 2] = w_blue_b

res_wpns = Image.fromarray(w_arr)
res_wpns.save(out_dir / "cha_breakdown_gs_wpns_a.png")
print("[+] Saved assets_redeco/cha_breakdown_gs_wpns_a.png!")

