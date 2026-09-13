import UnityPy
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

um_env = UnityPy.load("extracted_apk/assets/assetpack/ultramagnus_gs_leader_odr/ultramagnus_gs_leader.assetbundle")

mesh_export = None
um_main_img = None
tform_misc_img = None

for o in um_env.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_ultramagnus_gs_leader_00":
        mesh_export = o.read().export()
    elif o.type.name == "Texture2D" and o.read_typetree().get("m_Name") == "cha_ultramagnus_gs_leader_main_a":
        um_main_img = o.read().image
    elif o.type.name == "Texture2D" and o.read_typetree().get("m_Name") == "tform_misc_A":
        tform_misc_img = o.read().image

w, h = um_main_img.size
orig_arr = np.array(um_main_img.convert("RGBA"), dtype=np.float32)
or_r, or_g, or_b, or_a = orig_arr[..., 0], orig_arr[..., 1], orig_arr[..., 2], orig_arr[..., 3]
lum = (or_r * 0.299 + or_g * 0.587 + or_b * 0.114) / 255.0

verts = []
vts = []
for line in mesh_export.splitlines():
    if line.startswith('v '):
        p = line.split()
        verts.append([float(p[1]), float(p[2]), float(p[3])])
    elif line.startswith('vt '):
        p = line.split()
        vts.append([float(p[1]), float(p[2])])

verts = np.array(verts)
vts = np.array(vts)

mask_helmet = Image.new('L', (w, h), 0)
mask_face = Image.new('L', (w, h), 0)
mask_chest = Image.new('L', (w, h), 0)
mask_shoulders = Image.new('L', (w, h), 0)
mask_biceps = Image.new('L', (w, h), 0)
mask_forearms = Image.new('L', (w, h), 0)
mask_waist = Image.new('L', (w, h), 0)
mask_knees = Image.new('L', (w, h), 0)
mask_shin_panels = Image.new('L', (w, h), 0)

draw_helmet = ImageDraw.Draw(mask_helmet)
draw_face = ImageDraw.Draw(mask_face)
draw_chest = ImageDraw.Draw(mask_chest)
draw_shoulders = ImageDraw.Draw(mask_shoulders)
draw_biceps = ImageDraw.Draw(mask_biceps)
draw_forearms = ImageDraw.Draw(mask_forearms)
draw_waist = ImageDraw.Draw(mask_waist)
draw_knees = ImageDraw.Draw(mask_knees)
draw_shin_panels = ImageDraw.Draw(mask_shin_panels)

for line in mesh_export.splitlines():
    if line.startswith('f '):
        parts = line.split()[1:]
        face_data = []
        for p in parts:
            vals = p.split('/')
            vi = int(vals[0]) - 1
            vti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else None
            face_data.append((vi, vti))
        
        f_vis = [vi for vi, vti in face_data]
        f_verts = verts[f_vis]
        cy = f_verts[:, 1].mean()
        cz = f_verts[:, 2].mean()
        cx = f_verts[:, 0].mean()

        pts = []
        for vi, vti in face_data:
            if vti is not None:
                u, v = vts[vti]
                px = int(np.clip(u * w, 0, w - 1))
                py = int(np.clip((1.0 - v) * h, 0, h - 1))
                pts.append((px, py))
        if len(pts) < 3: continue

        # Head classification
        if cy >= 10.5:
            if 10.65 <= cy < 11.5 and cz >= 0.15 and abs(cx) <= 0.28:
                draw_face.polygon(pts, fill=255)
            else:
                draw_helmet.polygon(pts, fill=255)
        # Shoulders vs Chest
        elif 7.8 <= cy < 10.5:
            if abs(cx) > 2.0:
                draw_shoulders.polygon(pts, fill=255)
            else:
                draw_chest.polygon(pts, fill=255)
        # Biceps vs Upper Chest/Back
        elif 6.4 <= cy < 7.8:
            if abs(cx) > 1.8:
                draw_biceps.polygon(pts, fill=255)
            else:
                draw_chest.polygon(pts, fill=255)
        # Forearms vs Waist / Crotch
        elif 4.2 <= cy < 6.4:
            if abs(cx) > 1.8:
                draw_forearms.polygon(pts, fill=255)
            elif abs(cx) <= 1.3:
                draw_waist.polygon(pts, fill=255)
            elif cy <= 5.5 and cz >= 0.45:
                draw_knees.polygon(pts, fill=255)
        # Lower legs / Shins / Feet
        elif cy < 4.2:
            if 1.5 <= cy <= 3.8 and cz >= 1.30 and 0.5 <= abs(cx) <= 1.7:
                draw_shin_panels.polygon(pts, fill=255)
            elif cy >= 3.8 and cz >= 0.45 and abs(cx) <= 1.8:
                draw_knees.polygon(pts, fill=255)

m_helmet = np.array(mask_helmet) > 0
m_face = np.array(mask_face) > 0
m_chest = np.array(mask_chest) > 0
m_shoulders = np.array(mask_shoulders) > 0
m_biceps = np.array(mask_biceps) > 0
m_forearms = np.array(mask_forearms) > 0
m_waist = np.array(mask_waist) > 0
m_knees = np.array(mask_knees) > 0
m_shin_panels = np.array(mask_shin_panels) > 0

# Forehead crest
m_helmet[:122, :250] = m_helmet[:122, :250] | m_face[:122, :250]
m_face[:122, :250] = False

# Optics
is_optics = m_face & (or_g > 155) & (or_b > 175) & (or_r < 80)
optics_img = Image.fromarray((is_optics * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
m_optics = np.array(optics_img) > 0
m_face_bone = m_face & (~m_optics)

# Colors
red_r = np.clip(lum * 195.0 + 55.0, 0, 255)
red_g = np.clip(lum * 25.0 + 8.0, 0, 255)
red_b = np.clip(lum * 25.0 + 8.0, 0, 255)

blue_r = np.clip(lum * 30.0 + 10.0, 0, 255)
blue_g = np.clip(lum * 70.0 + 25.0, 0, 255)
blue_b = np.clip(lum * 200.0 + 50.0, 0, 255)

skull_r = np.clip(lum * 210.0 + 40.0, 0, 255)
skull_g = np.clip(lum * 205.0 + 38.0, 0, 255)
skull_b = np.clip(lum * 195.0 + 35.0, 0, 255)
is_crevice = m_face_bone & (lum < 0.35)
crevice_r = np.clip(lum * 40.0 + 15.0, 0, 255)
crevice_g = np.clip(lum * 40.0 + 15.0, 0, 255)
crevice_b = np.clip(lum * 40.0 + 15.0, 0, 255)

cyan_r = np.clip(lum * 20.0 + 80.0, 0, 255)
cyan_g = np.clip(lum * 40.0 + 220.0, 0, 255)
cyan_b = np.clip(lum * 40.0 + 235.0, 0, 255)

silver_r = np.clip(lum * 170.0 + 25.0, 0, 255)
silver_g = np.clip(lum * 175.0 + 25.0, 0, 255)
silver_b = np.clip(lum * 185.0 + 28.0, 0, 255)

purple_r = np.clip(lum * 180.0 + 40.0, 0, 255)
purple_g = np.clip(lum * 20.0 + 5.0, 0, 255)
purple_b = np.clip(lum * 240.0 + 50.0, 0, 255)

# 1. Base body is blue
is_joint = (lum < 0.18)
res_r = np.where(is_joint, silver_r, blue_r)
res_g = np.where(is_joint, silver_g, blue_g)
res_b = np.where(is_joint, silver_b, blue_b)

# 2. Red components (helmet, shoulders, forearms, knees, shins) excluding biceps and waist
red_parts = (m_shoulders | m_forearms | m_knees | m_shin_panels | m_helmet) & (~m_biceps) & (~m_waist) & (~m_face_bone) & (~m_optics)
res_r = np.where(red_parts, red_r, res_r)
res_g = np.where(red_parts, red_g, res_g)
res_b = np.where(red_parts, red_b, res_b)

# 3. Biceps and Waist are explicitly BLUE!
res_r = np.where(m_biceps | m_waist, blue_r, res_r)
res_g = np.where(m_biceps | m_waist, blue_g, res_g)
res_b = np.where(m_biceps | m_waist, blue_b, res_b)

# 4. Face is bone skull white
res_r = np.where(m_face_bone, np.where(is_crevice, crevice_r, skull_r), res_r)
res_g = np.where(m_face_bone, np.where(is_crevice, crevice_g, skull_g), res_g)
res_b = np.where(m_face_bone, np.where(is_crevice, crevice_b, skull_b), res_b)

# 5. Optics
res_r = np.where(m_optics, cyan_r, res_r)
res_g = np.where(m_optics, cyan_g, res_g)
res_b = np.where(m_optics, cyan_b, res_b)

# 6. Autobot symbol
is_original_red_insignia = (or_r > 130) & (or_g < 60) & (or_b < 60) & (lum < 0.5)
res_r = np.where(is_original_red_insignia, purple_r, res_r)
res_g = np.where(is_original_red_insignia, purple_g, res_g)
res_b = np.where(is_original_red_insignia, purple_b, res_b)

final_main = Image.fromarray(np.stack([res_r, res_g, res_b, or_a], axis=-1).astype(np.uint8))
final_main.save("assets_redeco/cha_ultramagnus_sg_leader_main_a.png")
print("Saved updated main texture!")

# Now synthesize tform_misc_A:
tf_arr = np.array(tform_misc_img.convert("RGBA"), dtype=np.float32)
tr, tg, tb, ta = tf_arr[..., 0], tf_arr[..., 1], tf_arr[..., 2], tf_arr[..., 3]
tlum = (tr * 0.299 + tg * 0.587 + tb * 0.114) / 255.0

# Blue for truck parts
t_blue_r = np.clip(tlum * 30.0 + 10.0, 0, 255)
t_blue_g = np.clip(tlum * 70.0 + 25.0, 0, 255)
t_blue_b = np.clip(tlum * 200.0 + 50.0, 0, 255)

# Red for red stripes/bumpers
t_red_r = np.clip(tlum * 195.0 + 55.0, 0, 255)
t_red_g = np.clip(tlum * 25.0 + 8.0, 0, 255)
t_red_b = np.clip(tlum * 25.0 + 8.0, 0, 255)

# Purple for insignia
t_purple_r = np.clip(tlum * 180.0 + 40.0, 0, 255)
t_purple_g = np.clip(tlum * 20.0 + 5.0, 0, 255)
t_purple_b = np.clip(tlum * 240.0 + 50.0, 0, 255)

# In original tform_misc_A:
# White panels: tr > 150, tg > 150, tb > 150
is_white_panel = (tr > 140) & (tg > 140) & (tb > 140) & (abs(tr - tg) < 30)
# Light blue cab parts: tb > tg and tb > tr and tb > 100
is_light_blue = (tb > 130) & (tb > tr + 40)
# Original red parts: tr > tb + 50 and tr > tg + 50
is_red_part = (tr > tb + 50) & (tr > tg + 50)
# Insignia: small red patch with emblem
# Tires: dark rubber tlum < 0.2
is_tire = (tlum < 0.2)

new_tr = np.where(is_white_panel | is_light_blue, t_blue_r, tr)
new_tg = np.where(is_white_panel | is_light_blue, t_blue_g, tg)
new_tb = np.where(is_white_panel | is_light_blue, t_blue_b, tb)

new_tr = np.where(is_red_part, t_red_r, new_tr)
new_tg = np.where(is_red_part, t_red_g, new_tg)
new_tb = np.where(is_red_part, t_red_b, new_tb)

# Insignia detection on tform
is_tf_insignia = is_red_part & (tlum < 0.45)
new_tr = np.where(is_tf_insignia, t_purple_r, new_tr)
new_tg = np.where(is_tf_insignia, t_purple_g, new_tg)
new_tb = np.where(is_tf_insignia, t_purple_b, new_tb)

final_tform = Image.fromarray(np.stack([new_tr, new_tg, new_tb, ta], axis=-1).astype(np.uint8))
final_tform.save("assets_redeco/cha_ultramagnus_sg_leader_tform_misc_a.png")
print("Saved synthesized tform_misc_A texture!")
