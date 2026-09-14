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
   - Forearm Car Doors: Clean Pearl White (#F4F6F8)
   - Rear Wheels & Tire Treads: Solid Matte Black (#121316)
   - Ankle Collars: Deep Navy Blue (#1A1B6B)
2. cha_breakdown_gs_main_a.png (1024x1024)
   - Clean White armor, Royal Blue limbs, Orange-Red faceplate with ruby optics.
   - Forearm Outer Car Doors: Clean Pearl White (#F4F6F8)
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import sys

try:
    import UnityPy
except ImportError:
    UnityPy = None

out_dir = Path("assets_redeco")
out_dir.mkdir(exist_ok=True)

# -------------------------------------------------------------
# Color Definitions
# -------------------------------------------------------------
C_WHITE = (244, 246, 248)          # Pearl white body
C_HOOD_RED = (216, 32, 24)          # Iconic G1 hood red (#D82018)
C_NAVY_PURPLE = (26, 27, 107)       # Stunticon accent navy-purple / deep navy (#1A1B6B)
C_BLACK_WINDOW = (13, 14, 18)       # Blacked-out window glass (#0D0E12)
C_GRILLE_BLACK = (21, 21, 21)       # Matte black front grille (#151515)
C_GUNMETAL = (36, 38, 42)           # Dark charcoal / gunmetal for roof pod (#24262A)
C_TAILLIGHT_RED = (230, 24, 16)     # Saturated red taillights (#E61810)
C_WHEEL_BLACK = (18, 19, 22)        # Solid matte black for wheels/tires

# -------------------------------------------------------------
# 1. Update cha_breakdown_gs_main_a.png (1024x1024)
# -------------------------------------------------------------
main_path = out_dir / "cha_breakdown_gs_main_a.png"
if not main_path.is_file():
    print("[-] cha_breakdown_gs_main_a.png not found in assets_redeco!")
    sys.exit(1)

main_img = Image.open(main_path).convert("RGBA")
arr0 = np.array(main_img).copy()
lum0 = (0.299 * arr0[:, :, 0] + 0.587 * arr0[:, :, 1] + 0.114 * arr0[:, :, 2]) / 255.0

# Forearm outer car door panel on main_a (x: 810..1024, y: 560..1024)
# Make clean Pearl White preserving shading
door_mask0 = np.zeros((1024, 1024), dtype=bool)
door_mask0[560:1024, 810:1024] = True
door_mask0 &= (lum0 > 0.05)

w0_r = np.clip(lum0 * 45 + 210, 0, 255).astype(np.uint8)
w0_g = np.clip(lum0 * 45 + 210, 0, 255).astype(np.uint8)
w0_b = np.clip(lum0 * 45 + 212, 0, 255).astype(np.uint8)

arr0[door_mask0, 0] = w0_r[door_mask0]
arr0[door_mask0, 1] = w0_g[door_mask0]
arr0[door_mask0, 2] = w0_b[door_mask0]

res_main = Image.fromarray(arr0)
res_main.save(main_path)
print("[+] Successfully updated assets_redeco/cha_breakdown_gs_main_a.png (Forearm doors -> White)!")

# -------------------------------------------------------------
# 2. Update cha_breakdown_gs_tform_misc_a.png (512x512)
# -------------------------------------------------------------
# Load base tform_misc_A
base_misc = None
base_candidates = [
    Path("scratch_sideswipe_textures/tform_misc_A.png"),
    Path(r"C:\Users\lenovo\.gemini\antigravity\brain\18bc91db-a40c-4e5f-bd62-8785fded8460\scratch\base_sideswipe\tform_misc_A.png"),
]
for cand in base_candidates:
    if cand.is_file():
        base_misc = Image.open(cand).convert("RGBA")
        break

if base_misc is None:
    # Extract from assetpack
    bundle_path = Path("extracted_apk/assets/assetpack/sideswipe_gs_odr/sideswipe_gs.assetbundle")
    if bundle_path.is_file() and UnityPy:
        env = UnityPy.load(str(bundle_path))
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                d = obj.read()
                if getattr(d, 'm_Name', getattr(d, 'name', '')) == "tform_misc_A":
                    base_misc = d.image.convert("RGBA")
                    break

if base_misc is None:
    print("[-] Could not load base tform_misc_A.png!")
    sys.exit(1)

W, H = base_misc.size # 512, 512
arr = np.array(base_misc).copy()
r = arr[:, :, 0].astype(float)
g = arr[:, :, 1].astype(float)
b = arr[:, :, 2].astype(float)

# Identify cyan windows in original texture
cyan_mask = (g > 180) & (b > 180) & (r < 60)

# Identify red car body on top half (y < 256)
top_half = np.zeros((H, W), dtype=bool)
top_half[:256, :] = True
red_body_mask = top_half & (r > 130) & (g < 70) & (b < 70)

# Also on bottom half, parts of car body
bottom_half_red = (~top_half) & (r > 140) & (g < 60) & (b < 60)

# Convert all red car body to clean Pearl White (preserving shading/luminance)
lum = 0.299 * (r / 255.0) + 0.587 * (g / 255.0) + 0.114 * (b / 255.0)
w_factor = np.clip((lum - 0.2) / 0.4, 0.0, 1.0)
white_r = np.clip(220 + w_factor * 32, 0, 255).astype(np.uint8)
white_g = np.clip(222 + w_factor * 32, 0, 255).astype(np.uint8)
white_b = np.clip(225 + w_factor * 30, 0, 255).astype(np.uint8)

arr[red_body_mask, 0] = white_r[red_body_mask]
arr[red_body_mask, 1] = white_g[red_body_mask]
arr[red_body_mask, 2] = white_b[red_body_mask]

arr[bottom_half_red, 0] = white_r[bottom_half_red]
arr[bottom_half_red, 1] = white_g[bottom_half_red]
arr[bottom_half_red, 2] = white_b[bottom_half_red]

# Clear any old markings on front hood (x: 0..110, y: 64..165)
hood_area = np.zeros((H, W), dtype=bool)
hood_area[64:170, :110] = True
hood_non_dark = hood_area & (lum > 0.15)
arr[hood_non_dark, 0] = white_r[hood_non_dark]
arr[hood_non_dark, 1] = white_g[hood_non_dark]
arr[hood_non_dark, 2] = white_b[hood_non_dark]

res_img = Image.fromarray(arr)
draw = ImageDraw.Draw(res_img)

# A. Windows: Turn ALL cyan windows to Solid Black
draw.polygon([(96, 120), (140, 96), (224, 96), (224, 155), (140, 155)], fill=(*C_BLACK_WINDOW, 255))
draw.polygon([(224, 96), (480, 64), (480, 115), (224, 115)], fill=(*C_BLACK_WINDOW, 255))
draw.polygon([(280, 280), (380, 280), (380, 380), (280, 380)], fill=(*C_BLACK_WINDOW, 255))
img_arr = np.array(res_img)
img_arr[cyan_mask, 0] = C_BLACK_WINDOW[0]
img_arr[cyan_mask, 1] = C_BLACK_WINDOW[1]
img_arr[cyan_mask, 2] = C_BLACK_WINDOW[2]
res_img = Image.fromarray(img_arr)
draw = ImageDraw.Draw(res_img)

# B. Front Hood: Big Solid Red Rectangle / Block (#D82018)
hood_red_poly = [(0, 72), (80, 72), (80, 160), (0, 160)]
draw.polygon(hood_red_poly, fill=(*C_HOOD_RED, 255))

# C. Front Lower Grille: Black (#151515) & Chin Splitter: Navy Purple
draw.rectangle([(0, 224), (45, 255)], fill=(*C_GRILLE_BLACK, 255))
draw.rectangle([(45, 224), (75, 255)], fill=(*C_NAVY_PURPLE, 255))
draw.polygon([(0, 195), (32, 195), (32, 224), (0, 224)], fill=(*C_NAVY_PURPLE, 255))

# D. Wheel Arches & Lower Side Skirts: Navy Purple (#1A1B6B)
draw.rectangle([(75, 226), (480, 246)], fill=(*C_NAVY_PURPLE, 255))
draw.arc([(70, 172), (160, 230)], start=180, end=0, fill=(*C_NAVY_PURPLE, 255), width=7)
draw.arc([(385, 172), (475, 230)], start=180, end=0, fill=(*C_NAVY_PURPLE, 255), width=7)

# E. Side Door Intake: Parallel Navy Purple Horizontal Stripes
stripe1 = [(235, 168), (380, 168), (370, 174), (245, 174)]
stripe2 = [(250, 180), (370, 180), (360, 186), (260, 186)]
draw.polygon(stripe1, fill=(*C_NAVY_PURPLE, 255))
draw.polygon(stripe2, fill=(*C_NAVY_PURPLE, 255))

# F. Roof Cannon / Engine Assembly: Dark Gunmetal (#24262A)
draw.rectangle([(275, 0), (420, 58)], fill=(*C_GUNMETAL, 255))
draw.rectangle([(130, 0), (275, 30)], fill=(*C_GUNMETAL, 255))

# G. Car Rear: Red Taillights, Navy Purple Plate & Bumper
draw.ellipse([(138, 54), (162, 74)], fill=(*C_TAILLIGHT_RED, 255), outline=(100, 10, 10, 255))
draw.ellipse([(168, 54), (192, 74)], fill=(*C_TAILLIGHT_RED, 255), outline=(100, 10, 10, 255))
draw.rectangle([(195, 52), (252, 74)], fill=(*C_NAVY_PURPLE, 255))
draw.rectangle([(480, 226), (512, 255)], fill=(*C_NAVY_PURPLE, 255))

# H. Rear Spoiler / Wing: Navy Purple Tips
draw.rectangle([(448, 15), (512, 45)], fill=(*C_NAVY_PURPLE, 255))
draw.rectangle([(0, 28), (40, 48)], fill=(*C_NAVY_PURPLE, 255))

# -------------------------------------------------------------
# I. ROBOT MODE OPTIMIZATIONS (Doors -> White, Wheels -> Black, Ankles -> Navy)
# -------------------------------------------------------------
arr_misc = np.array(res_img).copy()
lum_misc = (0.299 * arr_misc[:, :, 0] + 0.587 * arr_misc[:, :, 1] + 0.114 * arr_misc[:, :, 2]) / 255.0

# 1. Forearm Car Doors (Bottom right quadrant x: 258..510, y: 280..510) -> Pearl White
door_mask1 = np.zeros((H, W), dtype=bool)
door_mask1[280:H, 258:W] = True
door_mask1 &= (lum_misc > 0.05)

w1_r = np.clip(lum_misc * 45 + 210, 0, 255).astype(np.uint8)
w1_g = np.clip(lum_misc * 45 + 210, 0, 255).astype(np.uint8)
w1_b = np.clip(lum_misc * 45 + 212, 0, 255).astype(np.uint8)

arr_misc[door_mask1, 0] = w1_r[door_mask1]
arr_misc[door_mask1, 1] = w1_g[door_mask1]
arr_misc[door_mask1, 2] = w1_b[door_mask1]

# 2. Extract 3D Mesh Geometry for exact Wheels and Ankles
mesh_bundle = Path("assets_redeco/breakdown_gs.assetbundle")
if mesh_bundle.is_file() and UnityPy:
    env_m = UnityPy.load(str(mesh_bundle))
    mesh_obj = next(obj for obj in env_m.objects if obj.path_id == -296815002598429789)
    d = mesh_obj.read()
    obj_str = d.export()

    verts = []
    vts = []
    submeshes = {}
    curr_g = "default"

    for line in obj_str.splitlines():
        if line.startswith("v "):
            verts.append([float(p) for p in line[2:].split()])
        elif line.startswith("vt "):
            vts.append([float(p) for p in line[3:].split()])
        elif line.startswith("g "):
            curr_g = line.strip()
            if curr_g not in submeshes:
                submeshes[curr_g] = []
        elif line.startswith("f "):
            face = []
            for token in line[2:].split():
                sub = token.split("/")
                vi = int(sub[0]) - 1
                vti = int(sub[1]) - 1 if len(sub) > 1 and sub[1] else None
                face.append((vi, vti))
            if curr_g in submeshes:
                submeshes[curr_g].append(face)

    sm1 = submeshes.get("g cha_sideswipe_GS_Deluxe2008_00_1", [])

    rear_wheel_img = Image.new("L", (W, H), 0)
    draw_rw = ImageDraw.Draw(rear_wheel_img)
    side_wheel_tread_img = Image.new("L", (W, H), 0)
    draw_sw = ImageDraw.Draw(side_wheel_tread_img)
    ankle_img = Image.new("L", (W, H), 0)
    draw_ank = ImageDraw.Draw(ankle_img)

    for f in sm1:
        cx = sum(verts[v[0]][0] for v in f) / len(f)
        cy = sum(verts[v[0]][1] for v in f) / len(f)
        cz = sum(verts[v[0]][2] for v in f) / len(f)
        pts = [(int(round(vts[v[1]][0] * (W - 1))), int(round((1.0 - vts[v[1]][1]) * (H - 1)))) for v in f if v[1] is not None]
        if len(pts) >= 3:
            # Rear wheels behind calves:
            if cz < -0.3 and 0.8 < cy < 2.5:
                draw_rw.polygon(pts, fill=255)
            # Side wheels:
            elif abs(cx) > 0.85 and 0.8 < cy < 2.5 and abs(cz) < 0.3:
                draw_sw.polygon(pts, fill=255)
            # Ankle collar:
            elif 0.55 <= cy <= 1.1:
                draw_ank.polygon(pts, fill=255)

    rw_mask = np.array(rear_wheel_img) > 0
    sw_mask = np.array(side_wheel_tread_img) > 0
    ank_mask = np.array(ankle_img) > 0

    # A. Rear Wheels -> Solid Matte Black
    arr_misc[rw_mask, 0] = C_WHEEL_BLACK[0]
    arr_misc[rw_mask, 1] = C_WHEEL_BLACK[1]
    arr_misc[rw_mask, 2] = C_WHEEL_BLACK[2]

    # B. Side Wheel Treads -> Solid Matte Black
    tread_mask = (sw_mask & (lum_misc < 0.45)) | (sw_mask & (np.arange(H)[:, None] > 480))
    arr_misc[tread_mask, 0] = C_WHEEL_BLACK[0]
    arr_misc[tread_mask, 1] = C_WHEEL_BLACK[1]
    arr_misc[tread_mask, 2] = C_WHEEL_BLACK[2]

    # C. Ankle Collars -> Deep Navy Blue (#1A1B6B)
    ank_mask &= (~rw_mask)
    dilated_ank = Image.fromarray(ank_mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(size=3))
    ank_mask = (np.array(dilated_ank) > 0) & (~rw_mask)

    navy_r = np.clip(lum_misc * 25 + 18, 0, 255).astype(np.uint8)
    navy_g = np.clip(lum_misc * 25 + 20, 0, 255).astype(np.uint8)
    navy_b = np.clip(lum_misc * 50 + 95, 0, 255).astype(np.uint8)

    arr_misc[ank_mask, 0] = navy_r[ank_mask]
    arr_misc[ank_mask, 1] = navy_g[ank_mask]
    arr_misc[ank_mask, 2] = navy_b[ank_mask]

# Save final tform_misc_a
res_final_misc = Image.fromarray(arr_misc)
misc_path = out_dir / "cha_breakdown_gs_tform_misc_a.png"
res_final_misc.save(misc_path)
print("[+] Successfully generated calibrated assets_redeco/cha_breakdown_gs_tform_misc_a.png!")
