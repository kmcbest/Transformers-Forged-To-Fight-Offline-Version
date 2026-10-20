from PIL import Image
import numpy as np

nem_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_nemesisprime_gs_voyager2015_main_a.png"
opt_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_main_a.png"
brain = r"C:\Users\Xiangli496\.gemini\antigravity\brain\76f5ec0f-a15b-490d-aeb0-5237fdbedbfa"

nem_arr = np.array(Image.open(nem_path).convert("RGB"), dtype=np.float32)
opt_arr = np.array(Image.open(opt_path).convert("RGB"), dtype=np.float32)

H, W, _ = nem_arr.shape
yy, xx = np.mgrid[0:H, 0:W]

# Luminance from Nemesis for fine surface detail, bevels, and ambient occlusion
lum = (0.299 * nem_arr[:, :, 0] + 0.587 * nem_arr[:, :, 1] + 0.114 * nem_arr[:, :, 2]) / 255.0
lum_detail = np.power(np.clip(lum * 1.30, 0.05, 1.0), 0.85)

# Target Color Palette (Normalized 0..1 RGB)
COL_ACID_GREEN   = np.array([0.72, 0.88, 0.08])  # #B7E114 Bright Fluorescent Acid Green
COL_DARK_PURPLE  = np.array([0.31, 0.10, 0.36])  # #4F1A5C Deep Poison Purple
COL_LILAC_PURPLE = np.array([0.56, 0.38, 0.62])  # #8F619E Lilac / Lavender Metallic Purple (Faceplate)
COL_GUNMETAL     = np.array([0.58, 0.62, 0.65])  # #949EA6 Metallic Gunmetal Silver
COL_WINDSHIELD   = np.array([0.78, 0.10, 0.12])  # #C71A1E Deep Crimson Red Glass
COL_OPTICS_AMBER = np.array([1.00, 0.45, 0.05])  # #FF730D Glowing Amber/Red Optics
COL_CREST_LIME   = np.array([0.75, 0.92, 0.06])  # #C0EB10 Bright Lime Forehead Crest

out_arr = np.copy(nem_arr)

def tint(mask, col, base=0.35, high=0.65):
    for c in range(3):
        out_arr[mask, c] = np.clip((col[c] * 255.0) * (base + high * lum_detail[mask]), 0, 255)

# 1. HEAD REGION (X < 260, Y < 270)
is_head_box = (xx < 260) & (yy < 270)
is_opt_blue = (opt_arr[:, :, 2] > opt_arr[:, :, 0] + 15) & (opt_arr[:, :, 2] > opt_arr[:, :, 1] - 5)
is_opt_silver = (np.abs(opt_arr[:, :, 0] - opt_arr[:, :, 1]) < 18) & (np.abs(opt_arr[:, :, 1] - opt_arr[:, :, 2]) < 18) & (opt_arr[:, :, 0] > 60)

# Helmet Shell: Deep Purple
is_helmet = is_head_box & is_opt_blue
tint(is_helmet, COL_DARK_PURPLE, 0.30, 0.70)

# Forehead Crest / Brow: Lime Green
is_crest = is_head_box & (xx < 65) & (yy < 100)
tint(is_crest, COL_CREST_LIME, 0.40, 0.60)

# Faceplate: Lilac / Lavender Purple
is_faceplate = is_head_box & is_opt_silver & (xx < 145) & (yy > 130) & (yy < 260)
tint(is_faceplate, COL_LILAC_PURPLE, 0.35, 0.65)

# Cheek vents: Gunmetal
is_cheek_vent = is_head_box & is_opt_silver & (xx >= 145) & (xx < 195) & (yy > 150) & (yy < 235)
tint(is_cheek_vent, COL_GUNMETAL, 0.25, 0.75)

# Eyes: Glowing Amber/Red
is_eyes = is_head_box & (xx > 30) & (xx < 85) & (yy > 140) & (yy < 175) & (nem_arr[:, :, 0] > 70)
out_arr[is_eyes, 0] = 255
out_arr[is_eyes, 1] = 90
out_arr[is_eyes, 2] = 20

# 2. CHEST & WINDSHIELD (X < 450, Y in [360, 660])
# Exact clean rectangular windshield glass pane
is_windshield = (nem_arr[:, :, 0] > 160) & (nem_arr[:, :, 1] < 40) & (nem_arr[:, :, 2] < 40) & (xx < 400) & (yy > 400) & (yy < 700)
# Tint windshield deep crimson
tint(is_windshield, COL_WINDSHIELD, 0.20, 0.80)

# Add subtle spiderweb cracked glass pattern inside the windshield
yw, xw = np.where(is_windshield)
if len(yw) > 0:
    # Center of windshield glass is approximately (270, 567)
    cx_w, cy_w = 270.0, 567.0
    r = np.sqrt((xw - cx_w)**2 + (yw - cy_w)**2)
    theta = np.arctan2(yw - cy_w, xw - cx_w)
    cracks = (np.abs(np.sin(theta * 6.0)) > 0.94) | (np.abs(np.sin(r * 0.25)) > 0.94)
    # Highlight cracks in bright orange
    for c, val in enumerate([255, 170, 40]):
        out_arr[yw[cracks], c] = val

# Windshield frame & wipers (silver/chrome trim)
is_frame = (xx >= 200) & (xx <= 340) & (yy >= 480) & (yy <= 645) & (~is_windshield) & is_opt_silver
tint(is_frame, COL_GUNMETAL, 0.40, 0.60)

# Cab Armor surrounding the windshield: Acid Green
is_opt_red = (opt_arr[:, :, 0] > opt_arr[:, :, 1] + 25) & (opt_arr[:, :, 0] > opt_arr[:, :, 2] + 25)
is_cab_armor = is_opt_red & (xx < 450) & (yy >= 360) & (yy <= 660) & (~is_windshield) & (~is_frame)
tint(is_cab_armor, COL_ACID_GREEN, 0.38, 0.62)

# 3. FOREARMS & BICEPS & SHOULDERS (Acid Green)
# Forearms in Optimus are red
is_arms_red = is_opt_red & (xx >= 450)
tint(is_arms_red, COL_ACID_GREEN, 0.38, 0.62)

# Shoulder armor box (X in [670, 830], Y in [220, 380])
# Keep the Decepticon logo inside (purple) while painting the outer shell Acid Green
is_shoulder_box = (xx >= 670) & (xx <= 830) & (yy >= 220) & (yy <= 380)
is_decepticon_logo = is_shoulder_box & (nem_arr[:, :, 0] > 70) & (nem_arr[:, :, 2] > 70) & (nem_arr[:, :, 1] < 50)
is_shoulder_outer = is_shoulder_box & (~is_decepticon_logo)
tint(is_shoulder_outer, COL_ACID_GREEN, 0.38, 0.62)

# Hands: Deep Purple
is_hands = (xx >= 830) & (xx <= 960) & (yy >= 230) & (yy <= 360)
tint(is_hands, COL_DARK_PURPLE, 0.30, 0.70)

# 4. LOWER BODY & LEGS
# Shins (Front lower leg): Acid Green (where Optimus is blue, but NOT the feet)
is_shins = (xx >= 310) & (xx <= 520) & (yy >= 640) & (yy < 920) & is_opt_blue
tint(is_shins, COL_ACID_GREEN, 0.38, 0.62)

# Leg outer panels: Acid Green
is_leg_outer = (xx < 300) & (yy >= 640) & (yy < 920) & (is_opt_blue | is_opt_red)
tint(is_leg_outer, COL_ACID_GREEN, 0.38, 0.62)

# Feet & Toes: Deep Purple (Y >= 920)
is_feet = (yy >= 920) & (is_opt_blue | is_opt_silver)
tint(is_feet, COL_DARK_PURPLE, 0.30, 0.70)

# Pelvis / Crotch: Deep Purple
is_pelvis = (xx >= 340) & (xx <= 490) & (yy >= 930) & (yy <= 1024)
tint(is_pelvis, COL_DARK_PURPLE, 0.28, 0.72)

# Midriff Radiator Grill: Gunmetal Silver
is_midriff = (xx >= 330) & (xx <= 520) & (yy >= 350) & (yy <= 480) & is_opt_silver
tint(is_midriff, COL_GUNMETAL, 0.25, 0.75)

# Thighs: Gunmetal Silver
is_thighs = ((xx < 200) & (yy >= 260) & (yy <= 360)) | ((xx >= 330) & (xx <= 500) & (yy >= 200) & (yy <= 340))
tint(is_thighs & is_opt_silver, COL_GUNMETAL, 0.25, 0.75)

# Save result
result_img = Image.fromarray(out_arr.astype(np.uint8))
save_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\cha_toxitron_main_a.png"
result_img.save(save_path)
result_img.save(f"{brain}/toxitron_cleaned_texture.png")
print("[OK] Cleaned Toxitron texture saved successfully!")
