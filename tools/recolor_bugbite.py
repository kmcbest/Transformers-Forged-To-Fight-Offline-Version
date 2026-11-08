import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# 1. Main body texture: cha_bumblebee_gs_kabam_main_a
main_p = ROOT / "tools/dump_bb_tex/cha_bumblebee_gs_kabam_main_a.png"
im_main = Image.open(main_p).convert("RGBA")
arr = np.array(im_main)

r = arr[:, :, 0].astype(float)
g = arr[:, :, 1].astype(float)
b = arr[:, :, 2].astype(float)
a = arr[:, :, 3].astype(float)

# Detect yellow armor: high R, high G, low B
# Bumblebee yellow: R in [100, 255], G in [80, 255], B < 120
is_yellow = (r > 100) & (g > 70) & (b < 130) & (r - b > 40) & (g - b > 25)

# Convert yellow to Bug Bite pearl white / light metallic grey
# Compute luminance preserving highlights and shadows
lum = 0.299 * r + 0.587 * g + 0.114 * b
# Normalize luminance from Bumblebee's yellow range to white range [180, 245]
# lum typically ranges from ~60 to ~220
lum_norm = np.clip((lum - 50.0) / (220.0 - 50.0), 0.0, 1.0)
target_white = 175.0 + lum_norm * 70.0  # 175 to 245

# Detect eyes (Region 1: Y=[780, 862], X=[254, 362] with blue/cyan)
is_eyes = (b > 80) & (b > r + 20) & (np.arange(1024)[:, None] >= 770) & (np.arange(1024)[:, None] <= 870) & (np.arange(1024)[None, :] >= 240) & (np.arange(1024)[None, :] <= 370)

# Detect windows (Region 0: Y=[534, 666], X=[0, 248] with blue/cyan)
# Bug Bite windows in ChatGPT image: dark tinted violet/black
is_windows = (b > 80) & (b > r + 20) & (np.arange(1024)[:, None] >= 520) & (np.arange(1024)[:, None] <= 680) & (np.arange(1024)[None, :] >= 0) & (np.arange(1024)[None, :] <= 260)

# Detect Autobot badge at Y=[423, 514], X=[0, 49]
is_badge = (r > 130) & (g < 70) & (b < 70) & (np.arange(1024)[:, None] >= 420) & (np.arange(1024)[:, None] <= 520) & (np.arange(1024)[None, :] <= 55)

new_arr = arr.copy()

# Apply pearl white to yellow armor
for c_idx, tint in [(0, 1.0), (1, 0.98), (2, 0.99)]:  # Slight cool silver tint
    val = target_white * tint
    new_arr[:, :, c_idx] = np.where(is_yellow, np.clip(val, 0, 255).astype(np.uint8), new_arr[:, :, c_idx])

# Apply glowing RED to eyes
# Red eyes: vibrant crimson/ruby (R=255, G=20, B=25)
new_arr[:, :, 0] = np.where(is_eyes, 255, new_arr[:, :, 0])
new_arr[:, :, 1] = np.where(is_eyes, 20, new_arr[:, :, 1])
new_arr[:, :, 2] = np.where(is_eyes, 25, new_arr[:, :, 2])

# Apply tinted dark violet/charcoal to windows
win_lum = lum * 0.35  # dark tinted
new_arr[:, :, 0] = np.where(is_windows, np.clip(win_lum * 0.9 + 15, 0, 255).astype(np.uint8), new_arr[:, :, 0])
new_arr[:, :, 1] = np.where(is_windows, np.clip(win_lum * 0.7 + 10, 0, 255).astype(np.uint8), new_arr[:, :, 1])
new_arr[:, :, 2] = np.where(is_windows, np.clip(win_lum * 1.1 + 25, 0, 255).astype(np.uint8), new_arr[:, :, 2])

# Replace Autobot badge with Mercenary deep purple
# Mercenary purple: R=130, G=30, B=160
new_arr[:, :, 0] = np.where(is_badge, 130, new_arr[:, :, 0])
new_arr[:, :, 1] = np.where(is_badge, 30, new_arr[:, :, 1])
new_arr[:, :, 2] = np.where(is_badge, 160, new_arr[:, :, 2])

out_main = ROOT / "assets_redeco/cha_bugbite_gs_main_a.png"
Image.fromarray(new_arr).save(out_main)
print(f"[+] Saved custom Bug Bite main texture -> {out_main}")

# 2. Vehicle mode misc texture: tform_misc_A
tform_p = ROOT / "tools/dump_bb_tex/tform_misc_A.png"
im_tform = Image.open(tform_p).convert("RGBA")
tarr = np.array(im_tform)

tr = tarr[:, :, 0].astype(float)
tg = tarr[:, :, 1].astype(float)
tb = tarr[:, :, 2].astype(float)

is_tyellow = (tr > 100) & (tg > 70) & (tb < 130) & (tr - tb > 40)
tlum = 0.299 * tr + 0.587 * tg + 0.114 * tb
tlum_norm = np.clip((tlum - 50.0) / (220.0 - 50.0), 0.0, 1.0)
target_twhite = 175.0 + tlum_norm * 70.0

new_tarr = tarr.copy()
for c_idx, tint in [(0, 1.0), (1, 0.98), (2, 0.99)]:
    val = target_twhite * tint
    new_tarr[:, :, c_idx] = np.where(is_tyellow, np.clip(val, 0, 255).astype(np.uint8), new_tarr[:, :, c_idx])

out_tform = ROOT / "assets_redeco/cha_bugbite_gs_tform_misc_a.png"
Image.fromarray(new_tarr).save(out_tform)
print(f"[+] Saved custom Bug Bite vehicle texture -> {out_tform}")

# 3. Weapons texture: cha_bumblebee_gs_kabam_wpns_a
wpns_p = ROOT / "tools/dump_bb_tex/cha_bumblebee_gs_kabam_wpns_a.png"
im_wpns = Image.open(wpns_p).convert("RGBA")
warr = np.array(im_wpns)
wr = warr[:, :, 0].astype(float)
wg = warr[:, :, 1].astype(float)
wb = warr[:, :, 2].astype(float)

is_wyellow = (wr > 100) & (wg > 70) & (wb < 130) & (wr - wb > 40)
wlum = 0.299 * wr + 0.587 * wg + 0.114 * wb
wlum_norm = np.clip((wlum - 50.0) / (220.0 - 50.0), 0.0, 1.0)
target_wwhite = 170.0 + wlum_norm * 70.0

new_warr = warr.copy()
for c_idx, tint in [(0, 0.95), (1, 0.95), (2, 1.0)]:
    val = target_wwhite * tint
    new_warr[:, :, c_idx] = np.where(is_wyellow, np.clip(val, 0, 255).astype(np.uint8), new_warr[:, :, c_idx])

out_wpns = ROOT / "assets_redeco/cha_bugbite_gs_wpns_a.png"
Image.fromarray(new_warr).save(out_wpns)
print(f"[+] Saved custom Bug Bite weapons texture -> {out_wpns}")

# 4. Emissive RAOE texture: main_tform_misc_RAOE
# Set eye region in RAOE to have high B (emissive) and A (Format 4 RGBA32)
raoe_p = ROOT / "tools/dump_bb_tex/main_tform_misc_RAOE.png"
im_raoe = Image.open(raoe_p).convert("RGBA")
rarr = np.array(im_raoe)
# In 512x512, eyes region Y=[385, 435], X=[120, 185]
is_raoe_eyes = (np.arange(512)[:, None] >= 385) & (np.arange(512)[:, None] <= 435) & (np.arange(512)[None, :] >= 120) & (np.arange(512)[None, :] <= 185)
# Set B channel and A channel to 200 for glowing eyes
rarr[:, :, 2] = np.where(is_raoe_eyes, 220, rarr[:, :, 2])
rarr[:, :, 3] = np.where(is_raoe_eyes, 220, 255)

out_raoe = ROOT / "assets_redeco/cha_bugbite_gs_raoe.png"
Image.fromarray(rarr).save(out_raoe)
print(f"[+] Saved custom Bug Bite RAOE texture -> {out_raoe}")
