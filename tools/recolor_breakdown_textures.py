#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recolor_breakdown_textures.py

Generates authentic G1 / Stunticon Breakdown (打击) textures:
1. cha_breakdown_gs_tform_misc_a.png (512x512)
   - Clean Pearl White car body
   - Front Hood: Solid Vibrant Red (#D82018) block
   - Front Grille: Matte Black (#151515)
   - Front Chin/Splitter corners: Navy Purple (#1A1B6B)
   - Windows: Deep Black (#0D0E12)
   - Wheel Arches & Side Skirts: Navy Purple (#1A1B6B)
   - Side Door Intake: Clean horizontal Navy Purple stripes (#1A1B6B)
   - Roof Pods/Cannons: Dark Gunmetal (#24262A)
   - Taillights: Bright Red (#E61810)
   - Rear Plate & Bumper corners: Navy Purple (#1A1B6B)
   - Spoiler Wingtips: Navy Purple (#1A1B6B)
2. cha_breakdown_gs_main_a.png (1024x1024)
   - Clean White armor, Royal Blue limbs, Orange-Red faceplate with ruby optics.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

out_dir = Path("assets_redeco")
out_dir.mkdir(exist_ok=True)

# Load base textures from extracted Sideswipe
base_misc = Image.open("scratch_sideswipe_textures/tform_misc_A.png").convert("RGBA")
W, H = base_misc.size # 512, 512

# Colors
C_WHITE = (244, 246, 248)       # Pearl white body
C_HOOD_RED = (216, 32, 24)       # Iconic G1 hood red (#D82018)
C_NAVY_PURPLE = (26, 27, 107)    # Stunticon accent navy-purple (#1A1B6B)
C_BLACK_WINDOW = (13, 14, 18)    # Blacked-out window glass (#0D0E12)
C_GRILLE_BLACK = (21, 21, 21)    # Matte black front grille (#151515)
C_GUNMETAL = (36, 38, 42)        # Dark charcoal / gunmetal for roof pod (#24262A)
C_TAILLIGHT_RED = (230, 24, 16)  # Saturated red taillights (#E61810)

arr = np.array(base_misc).copy()
r = arr[:, :, 0].astype(float)
g = arr[:, :, 1].astype(float)
b = arr[:, :, 2].astype(float)

# 1. Identify cyan windows in original texture
cyan_mask = (g > 180) & (b > 180) & (r < 60)

# 2. Identify red car body on top half (y < 256)
top_half = np.zeros((H, W), dtype=bool)
top_half[:256, :] = True
red_body_mask = top_half & (r > 130) & (g < 70) & (b < 70)

# Also on bottom half, some parts of the car body (like door panels / windshield frame)
bottom_half_red = (~top_half) & (r > 140) & (g < 60) & (b < 60)

# Convert all red car body on top half to clean Pearl White (preserving shading/luminance)
lum = 0.299 * (r / 255.0) + 0.587 * (g / 255.0) + 0.114 * (b / 255.0)

# For red body: map lum (around 0.2 to 0.6) to bright white [225..255]
w_factor = np.clip((lum - 0.2) / 0.4, 0.0, 1.0)
white_r = np.clip(220 + w_factor * 32, 0, 255).astype(np.uint8)
white_g = np.clip(222 + w_factor * 32, 0, 255).astype(np.uint8)
white_b = np.clip(225 + w_factor * 30, 0, 255).astype(np.uint8)

arr[red_body_mask, 0] = white_r[red_body_mask]
arr[red_body_mask, 1] = white_g[red_body_mask]
arr[red_body_mask, 2] = white_b[red_body_mask]

# Also bottom half car panels to white
arr[bottom_half_red, 0] = white_r[bottom_half_red]
arr[bottom_half_red, 1] = white_g[bottom_half_red]
arr[bottom_half_red, 2] = white_b[bottom_half_red]

# Clear any old Autobot logo or blue markings on front hood (x: 0..110, y: 64..165)
hood_area = np.zeros((H, W), dtype=bool)
hood_area[64:170, :110] = True
hood_non_dark = hood_area & (lum > 0.15)
arr[hood_non_dark, 0] = white_r[hood_non_dark]
arr[hood_non_dark, 1] = white_g[hood_non_dark]
arr[hood_non_dark, 2] = white_b[hood_non_dark]

# Convert array back to PIL Image for precise geometric painting
res_img = Image.fromarray(arr)
draw = ImageDraw.Draw(res_img)

# -------------------------------------------------------------
# A. Windows: Turn ALL cyan windows to Solid Black
# -------------------------------------------------------------
# Front windshield (top half)
draw.polygon([(96, 120), (140, 96), (224, 96), (224, 155), (140, 155)], fill=(*C_BLACK_WINDOW, 255))
# Side window (top half)
draw.polygon([(224, 96), (480, 64), (480, 115), (224, 115)], fill=(*C_BLACK_WINDOW, 255))
# Lower windshield / interior windows (bottom half)
draw.polygon([(280, 280), (380, 280), (380, 380), (280, 380)], fill=(*C_BLACK_WINDOW, 255))
# Direct mask overwrite for any stray cyan pixels
img_arr = np.array(res_img)
img_arr[cyan_mask, 0] = C_BLACK_WINDOW[0]
img_arr[cyan_mask, 1] = C_BLACK_WINDOW[1]
img_arr[cyan_mask, 2] = C_BLACK_WINDOW[2]
res_img = Image.fromarray(img_arr)
draw = ImageDraw.Draw(res_img)

# -------------------------------------------------------------
# B. Front Hood: Big Solid Red Rectangle / Block (#D82018)
# -------------------------------------------------------------
# On Sideswipe UV, front hood extends longitudinally x: 0..80, y: 72..160
hood_red_poly = [
    (0, 72),
    (80, 72),
    (80, 160),
    (0, 160),
]
draw.polygon(hood_red_poly, fill=(*C_HOOD_RED, 255))

# -------------------------------------------------------------
# C. Front Lower Grille: Black (#151515) & Chin Splitter: Navy Purple
# -------------------------------------------------------------
# Center lower intake grille is black
draw.rectangle([(0, 224), (45, 255)], fill=(*C_GRILLE_BLACK, 255))
# Front lower chin / splitter corner is navy purple
draw.rectangle([(45, 224), (75, 255)], fill=(*C_NAVY_PURPLE, 255))
draw.polygon([(0, 195), (32, 195), (32, 224), (0, 224)], fill=(*C_NAVY_PURPLE, 255))

# -------------------------------------------------------------
# D. Wheel Arches & Lower Side Skirts: Navy Purple (#1A1B6B)
# -------------------------------------------------------------
# Full length bottom side skirt strip: y = 224..252, x = 75..480
draw.rectangle([(75, 226), (480, 246)], fill=(*C_NAVY_PURPLE, 255))

# Front wheel arch rim (curved arch around x=75..155, y=175..224)
draw.arc([(70, 172), (160, 230)], start=180, end=0, fill=(*C_NAVY_PURPLE, 255), width=7)

# Rear wheel arch rim (curved arch around x=390..470, y=175..224)
draw.arc([(385, 172), (475, 230)], start=180, end=0, fill=(*C_NAVY_PURPLE, 255), width=7)

# -------------------------------------------------------------
# E. Side Door Intake: Parallel Navy Purple Horizontal Stripes
# -------------------------------------------------------------
# Door side intake scoop is located at x = 240..380, y = 160..195
stripe1 = [(235, 168), (380, 168), (370, 174), (245, 174)]
stripe2 = [(250, 180), (370, 180), (360, 186), (260, 186)]
draw.polygon(stripe1, fill=(*C_NAVY_PURPLE, 255))
draw.polygon(stripe2, fill=(*C_NAVY_PURPLE, 255))

# -------------------------------------------------------------
# F. Roof Cannon / Engine Assembly: Dark Gunmetal (#24262A)
# -------------------------------------------------------------
# Located at x = 280..420, y = 0..60
draw.rectangle([(275, 0), (420, 58)], fill=(*C_GUNMETAL, 255))
# Rear engine louvers / roof scoop base
draw.rectangle([(130, 0), (275, 30)], fill=(*C_GUNMETAL, 255))

# -------------------------------------------------------------
# G. Car Rear: Red Taillights, Navy Purple Plate & Bumper
# -------------------------------------------------------------
# 4 Round taillights: 2 on each side of the rear fascia
draw.ellipse([(138, 54), (162, 74)], fill=(*C_TAILLIGHT_RED, 255), outline=(100, 10, 10, 255))
draw.ellipse([(168, 54), (192, 74)], fill=(*C_TAILLIGHT_RED, 255), outline=(100, 10, 10, 255))

# Rear central plate between & around taillights: Navy Purple
draw.rectangle([(195, 52), (252, 74)], fill=(*C_NAVY_PURPLE, 255))

# Rear lower bumper corners: Navy Purple
draw.rectangle([(480, 226), (512, 255)], fill=(*C_NAVY_PURPLE, 255))

# -------------------------------------------------------------
# H. Rear Spoiler / Wing: Navy Purple Tips
# -------------------------------------------------------------
# Wing endplate at top right: x = 448..512, y = 15..50
draw.rectangle([(448, 15), (512, 45)], fill=(*C_NAVY_PURPLE, 255))
draw.rectangle([(0, 28), (40, 48)], fill=(*C_NAVY_PURPLE, 255))

# Save the calibrated texture
res_img.save(out_dir / "cha_breakdown_gs_tform_misc_a.png")
print("[+] Successfully generated calibrated assets_redeco/cha_breakdown_gs_tform_misc_a.png!")
