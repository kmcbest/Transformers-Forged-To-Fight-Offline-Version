from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# Load original Prowl textures
prowl_main = Image.open("scratch_prowl_main_a.png").convert("RGBA")
prowl_misc = Image.open("scratch_prowl_misc_a.png").convert("RGBA")
prowl_wpns = Image.open("scratch_prowl_wpns_a.png").convert("RGBA")

# Load Decepticon insignia
dec_logo = Image.open("scratch_clean_decepticon_logo.png").convert("RGBA")

# -------------------------------------------------------------
# 1. Recolor cha_wildrider_gs_deluxe2016_main_a (1024x1024)
# -------------------------------------------------------------
main_arr = np.array(prowl_main).copy()
w_m, h_m = prowl_main.size

# Identify white/light grey panels in Prowl:
# High brightness, low saturation
r_m = main_arr[:, :, 0].astype(float) / 255.0
g_m = main_arr[:, :, 1].astype(float) / 255.0
b_m = main_arr[:, :, 2].astype(float) / 255.0
mx = np.maximum(np.maximum(r_m, g_m), b_m)
mn = np.minimum(np.minimum(r_m, g_m), b_m)
sat = np.zeros_like(mx)
sat[mx > 1e-5] = (mx[mx > 1e-5] - mn[mx > 1e-5]) / mx[mx > 1e-5]
lum = 0.299 * r_m + 0.587 * g_m + 0.114 * b_m

is_white_panel = (lum > 0.45) & (sat < 0.25)

# Areas definition:
# A. Chest plate: x in [200, 360], y in [380, 780]
is_chest = np.zeros_like(is_white_panel)
is_chest[380:780, 200:360] = is_white_panel[380:780, 200:360]

# B. Head faceplate: x in [220, 320], y in [150, 300]
is_face = np.zeros_like(is_white_panel)
is_face[150:300, 220:320] = is_white_panel[150:300, 220:320]

# C. Head crest: in Prowl, crest was bright red at x in [310, 510], y in [0, 150]
is_crest = np.zeros_like(is_white_panel)
is_crest[:150, 310:510] = (main_arr[:150, 310:510, 0] > 180) & (main_arr[:150, 310:510, 1] < 60)

# D. Shoulders: x in [0, 110], y in [350, 600] and x in [900, 1024], y in [450, 750]
is_shoulder = np.zeros_like(is_white_panel)
is_shoulder[350:600, :110] = is_white_panel[350:600, :110]
is_shoulder[450:750, 900:] = is_white_panel[450:750, 900:]

# E. All other white panels: Dark Charcoal / Slate Black
is_other_white = is_white_panel & (~is_chest) & (~is_face) & (~is_shoulder)

# Target Dark Charcoal color: base #2B2E33 -> R: 43, G: 46, B: 51
# Modulate by lum so textures, shadows and panel lines remain visible:
dark_r = np.clip(lum * 65 + 18, 0, 255).astype(np.uint8)
dark_g = np.clip(lum * 68 + 20, 0, 255).astype(np.uint8)
dark_b = np.clip(lum * 75 + 24, 0, 255).astype(np.uint8)

main_arr[is_other_white, 0] = dark_r[is_other_white]
main_arr[is_other_white, 1] = dark_g[is_other_white]
main_arr[is_other_white, 2] = dark_b[is_other_white]

# Recolor Prowl's red crest to dark charcoal to match helmet dome
main_arr[is_crest, 0] = np.clip(lum[is_crest] * 65 + 18, 0, 255).astype(np.uint8)
main_arr[is_crest, 1] = np.clip(lum[is_crest] * 68 + 20, 0, 255).astype(np.uint8)
main_arr[is_crest, 2] = np.clip(lum[is_crest] * 75 + 24, 0, 255).astype(np.uint8)

# F. Faceplate: Crimson Red (#D01525)
face_r = np.clip(lum * 180 + 40, 0, 255).astype(np.uint8)
face_g = np.clip(lum * 25 + 5, 0, 255).astype(np.uint8)
face_b = np.clip(lum * 35 + 10, 0, 255).astype(np.uint8)
main_arr[is_face, 0] = face_r[is_face]
main_arr[is_face, 1] = face_g[is_face]
main_arr[is_face, 2] = face_b[is_face]

# G. Shoulders: Bright Crimson Red (#C81825)
sh_r = np.clip(lum * 175 + 35, 0, 255).astype(np.uint8)
sh_g = np.clip(lum * 25 + 5, 0, 255).astype(np.uint8)
sh_b = np.clip(lum * 35 + 10, 0, 255).astype(np.uint8)
main_arr[is_shoulder, 0] = sh_r[is_shoulder]
main_arr[is_shoulder, 1] = sh_g[is_shoulder]
main_arr[is_shoulder, 2] = sh_b[is_shoulder]

# Convert back to PIL for graphics overlay
res_main = Image.fromarray(main_arr)

# H. Clean up doors "POLICE" in main_a: x in [680, 850], y in [280, 520]
# In main_a, door section has "HIGHWAY PATROL POLICE" and police badge
# Paint over with clean dark charcoal
draw_m = ImageDraw.Draw(res_main)
# Sample dark charcoal: (46, 49, 54)
draw_m.rectangle([685, 275, 830, 510], fill=(44, 47, 52, 255))

# I. Chest plate: Replace Autobot insignia with Decepticon insignia
# UV island has mirror seam at x = 339.
# Erase old Autobot red pixels cleanly:
chest_r = main_arr[470:565, 300:345, 0].astype(float)
chest_g = main_arr[470:565, 300:345, 1].astype(float)
chest_b = main_arr[470:565, 300:345, 2].astype(float)

is_red_local = (chest_r > 115) & (chest_r > chest_g * 1.15) & (chest_r > chest_b * 1.15)
red_mask_img = Image.fromarray(is_red_local.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(size=5))
is_red_dilated = np.array(red_mask_img) > 0

ref_col = main_arr[470:565, 270:271, :3]
for y in range(is_red_dilated.shape[0]):
    for x in range(is_red_dilated.shape[1]):
        if is_red_dilated[y, x]:
            main_arr[470 + y, 300 + x, :3] = ref_col[y, 0]

res_main = Image.fromarray(main_arr)
draw_m = ImageDraw.Draw(res_main)

# Re-apply door cleanup on res_main
draw_m.rectangle([685, 275, 830, 510], fill=(44, 47, 52, 255))

# Half-logo for mirrored chest at x = 339:
W_dec, H_dec = dec_logo.size
half_dec = dec_logo.crop((0, 0, W_dec // 2, H_dec))
target_h = 66
target_w = int(half_dec.width * (target_h / half_dec.height))
half_resized = half_dec.resize((target_w, target_h), Image.Resampling.LANCZOS)
paste_x = 339 - target_w
paste_y = 486
res_main.paste(half_resized, (paste_x, paste_y), half_resized)

# Single blue chest vent decal on left chest (mirrored in 3D to right side):
blue_vent = (45, 95, 155, 255)
vent_border = (30, 65, 110, 255)
draw_m.rectangle([248, 575, 270, 625], fill=blue_vent, outline=vent_border, width=2)

# Save recolored main_a
res_main.save("assets_redeco/cha_wildrider_gs_deluxe2016_main_a.png")
print("[+] Saved assets_redeco/cha_wildrider_gs_deluxe2016_main_a.png!")

# -------------------------------------------------------------
# 2. Recolor cha_wildrider_gs_deluxe2016_tform_misc_a (512x512)
# -------------------------------------------------------------
misc_arr = np.array(prowl_misc).copy()
r_c = misc_arr[:, :, 0].astype(float) / 255.0
g_c = misc_arr[:, :, 1].astype(float) / 255.0
b_c = misc_arr[:, :, 2].astype(float) / 255.0
mx_c = np.maximum(np.maximum(r_c, g_c), b_c)
mn_c = np.minimum(np.minimum(r_c, g_c), b_c)
sat_c = np.zeros_like(mx_c)
sat_c[mx_c > 1e-5] = (mx_c[mx_c > 1e-5] - mn_c[mx_c > 1e-5]) / mx_c[mx_c > 1e-5]
lum_c = 0.299 * r_c + 0.587 * g_c + 0.114 * b_c

# A. Windows: in Prowl, windows are light blue (hue cyan/blue, sat 0.1~0.35, lum 0.6~0.9)
# y in [75, 160], x in [80, 460]
is_window = np.zeros_like(sat_c, dtype=bool)
for y in range(75, 160):
    for x in range(80, 460):
        if (b_c[y, x] > r_c[y, x] + 0.05) and (b_c[y, x] > 0.55):
            is_window[y, x] = True

# Dilate window mask slightly
w_img = Image.fromarray(is_window.astype(np.uint8)*255).filter(ImageFilter.MaxFilter(size=3))
is_window = np.array(w_img) > 0

# Tint windows to translucent crimson red glass
# R: 180~220, G: 25~45, B: 35~55
win_r = np.clip(lum_c * 170 + 45, 0, 255).astype(np.uint8)
win_g = np.clip(lum_c * 30 + 5, 0, 255).astype(np.uint8)
win_b = np.clip(lum_c * 40 + 10, 0, 255).astype(np.uint8)
misc_arr[is_window, 0] = win_r[is_window]
misc_arr[is_window, 1] = win_g[is_window]
misc_arr[is_window, 2] = win_b[is_window]

# B. White car body panels -> Dark Charcoal / Black
is_white_car = (lum_c > 0.45) & (sat_c < 0.25) & (~is_window)
# Do not overwrite brake calipers/wheels (at bottom y > 380, x < 200)
is_white_car[380:, :200] = False

dark_c_r = np.clip(lum_c * 65 + 18, 0, 255).astype(np.uint8)
dark_c_g = np.clip(lum_c * 68 + 20, 0, 255).astype(np.uint8)
dark_c_b = np.clip(lum_c * 75 + 24, 0, 255).astype(np.uint8)

misc_arr[is_white_car, 0] = dark_c_r[is_white_car]
misc_arr[is_white_car, 1] = dark_c_g[is_white_car]
misc_arr[is_white_car, 2] = dark_c_b[is_white_car]

res_misc = Image.fromarray(misc_arr)
draw_misc = ImageDraw.Draw(res_misc)

# C. Clean up doors with "POLICE" and star badge:
# x in [245, 420], y in [160, 235]
draw_misc.rectangle([245, 160, 420, 235], fill=(44, 47, 52, 255))

# D. Add crimson red racing stripe on lower side skirt:
# Along the bottom edge of doors: y in [228, 236], x in [250, 440]
draw_misc.rectangle([250, 226, 440, 234], fill=(200, 25, 35, 255))
# And on the other door symmetry: y in [160, 168], x in [250, 440]
draw_misc.rectangle([250, 162, 440, 170], fill=(200, 25, 35, 255))

res_misc.save("assets_redeco/cha_wildrider_gs_deluxe2016_tform_misc_a.png")
print("[+] Saved assets_redeco/cha_wildrider_gs_deluxe2016_tform_misc_a.png!")

# -------------------------------------------------------------
# 3. Recolor cha_wildrider_gs_deluxe2016_wpns_a (1024x1024)
# -------------------------------------------------------------
# Prowl's weapons are silver/white shotgun and police baton.
# In Wildrider, make them dark gunmetal gray / black.
wpns_arr = np.array(prowl_wpns).copy()
lum_w = (0.299 * wpns_arr[:, :, 0] + 0.587 * wpns_arr[:, :, 1] + 0.114 * wpns_arr[:, :, 2]) / 255.0
is_light_wpn = lum_w > 0.35

dark_w_r = np.clip(lum_w * 70 + 15, 0, 255).astype(np.uint8)
dark_w_g = np.clip(lum_w * 72 + 16, 0, 255).astype(np.uint8)
dark_w_b = np.clip(lum_w * 78 + 20, 0, 255).astype(np.uint8)

wpns_arr[is_light_wpn, 0] = dark_w_r[is_light_wpn]
wpns_arr[is_light_wpn, 1] = dark_w_g[is_light_wpn]
wpns_arr[is_light_wpn, 2] = dark_w_b[is_light_wpn]

res_wpns = Image.fromarray(wpns_arr)
res_wpns.save("assets_redeco/cha_wildrider_gs_deluxe2016_wpns_a.png")
print("[+] Saved assets_redeco/cha_wildrider_gs_deluxe2016_wpns_a.png!")
