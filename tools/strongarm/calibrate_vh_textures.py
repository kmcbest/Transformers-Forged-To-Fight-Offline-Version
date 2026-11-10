import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from pathlib import Path
from PIL import Image

ROOT = Path(r"E:\Agent\TFTF-blender")
ASSET_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Strongarm"
TEX_DIR = ROOT / "tools" / "strongarm" / "textures"

def load_rgba(name):
    return np.array(Image.open(ASSET_DIR / name).convert("RGBA"))

def save_both(name, arr, mode="RGBA"):
    im = Image.fromarray(arr.astype(np.uint8), mode=mode)
    im.save(ASSET_DIR / name)
    if (TEX_DIR / name).exists() or mode == "RGBA":
        im.save(TEX_DIR / name)

# 1. Calibrate cha_strongarm_vh_a.png (clean baked dark shadow smudge under roof lightbar + UV border bleed)
vh_a = load_rgba("cha_strongarm_vh_a.png")
H, W, _ = vh_a.shape

# Top-right roof white strip under lightbar: UV x=[0.84..0.91], PIL y=[0.11..0.32]
# Note: in strongarm_vehicle.png, right edge x=[0.91..1.0] is the blue stripe, [0.84..0.91] is white cab roof
# which has a baked dark-grey blob around y=[0.14..0.28], x=[0.85..0.91] where low-res RID lightbar sat.
y0, y1 = int(H * 0.11), int(H * 0.32)
x0, x1 = int(W * 0.84), int(W * 0.91)
roi = vh_a[y0:y1, x0:x1, :3].astype(np.float32)
# Detect desaturated grey shadow pixels (where max(R,G,B)-min(R,G,B) < 28 and 60 < lum < 225)
lum = roi.mean(axis=2)
chroma = roi.max(axis=2) - roi.min(axis=2)
smudge = (chroma < 30.0) & (lum > 70.0) & (lum < 228.0)
# Lift cleanly toward crisp police truck white (228, 232, 238) matching the clean roof corner!
target_white = np.array([228.0, 232.0, 238.0], dtype=np.float32)
roi[smudge] = roi[smudge] * 0.15 + target_white * 0.85
vh_a[y0:y1, x0:x1, :3] = np.clip(roi, 0, 255).astype(np.uint8)
print(f"Cleaned cab roof baked shadow smudge: lifted {int(smudge.sum())} pixels in x=[{x0}:{x1}], y=[{y0}:{y1}]")

# Notice UV island dark gutter outlines: gently replace pure-black/near-black UV outline strokes adjacent to bright white paint?
# Careful! Don't touch windshield/windows/tires/panel lines intentionally drawn black! Just leave black outlines intentional,
# only fixing the grey baked shadow smudge on the white roof.
save_both("cha_strongarm_vh_a.png", vh_a, "RGBA")

# 2. Calibrate cha_strongarm_vh_tform_misc_RAOE.png (Tone down Vehicle Emissive from 65 -> 22 to prevent 16x HDR blowout!)
vh_raoe = load_rgba("cha_strongarm_vh_tform_misc_RAOE.png")
rgb = vh_raoe[:, :, :3].astype(np.float32)

# Target Emissive max = 22 (22/255 * 16.0 = 1.38x HDR: saturated vivid red/cyan lightbar & headlights!)
em_old_max = int(vh_raoe[:, :, 2].max())
if em_old_max > 22:
    rgb[:, :, 2] = np.round(rgb[:, :, 2] * (22.0 / em_old_max))
# Also slightly raise paint roughness floor from 40 -> 62 so white hood looks like clean glossy enamel instead of mirror chrome
# Keep matte rubber tires high roughness (~200-220) untouched.
paint_mask = rgb[:, :, 0] < 100.0
rgb[paint_mask, 0] = np.maximum(rgb[paint_mask, 0], 62.0)

vh_raoe[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
save_both("cha_strongarm_vh_tform_misc_RAOE.png", vh_raoe, "RGBA")
print(f"Vehicle RAOE B (Emissive) calibrated: max {em_old_max} -> {int(vh_raoe[:,:,2].max())}, mean={vh_raoe[:,:,2].mean():.2f}")

# Composite calibrated 512x512 Vehicle RAOE into bottom-right quadrant [1536:2048, 1536:2048] of unified main_tform_misc_RAOE
main_raoe = load_rgba("cha_strongarm_main_tform_misc_RAOE.png")
mh, mw, _ = main_raoe.shape
q_resized = np.array(Image.fromarray(vh_raoe[:, :, :3], mode="RGB").resize((mw // 4, mh // 4), Image.LANCZOS))
main_raoe[mh - mh // 4 : mh, mw - mw // 4 : mw, :3] = q_resized
save_both("cha_strongarm_main_tform_misc_RAOE.png", main_raoe, "RGBA")
print(f"Updated unified cha_strongarm_main_tform_misc_RAOE bottom-right tile [{mh-mh//4}:{mh}, {mw-mw//4}:{mw}] Emissive max={int(q_resized[:,:,2].max())}")

# 3. Calibrate cha_strongarm_vh_NM.png B (Metallic): ensure bright white/blue enamel paint is dielectric (B <= 10)
vh_nm = load_rgba("cha_strongarm_vh_NM.png")
a_rgb = vh_a[:, :, :3].astype(np.float32)
white_or_blue_paint = (
    ((a_rgb[:, :, 0] > 195) & (a_rgb[:, :, 1] > 195) & (a_rgb[:, :, 2] > 195)) |  # crisp white body
    ((a_rgb[:, :, 2] > 150) & (a_rgb[:, :, 2] - a_rgb[:, :, 0] > 55))              # vivid royal blue stripe
)
nm_b = vh_nm[:, :, 2].astype(np.float32)
before_metal = nm_b[white_or_blue_paint].mean()
nm_b[white_or_blue_paint] = np.minimum(nm_b[white_or_blue_paint], 8.0)
vh_nm[:, :, 2] = np.clip(nm_b, 0, 255).astype(np.uint8)
save_both("cha_strongarm_vh_NM.png", vh_nm, "RGBA")
print(f"Vehicle NM.B (Metallic) on white/blue paint: {before_metal:.1f} -> {vh_nm[:,:,2][white_or_blue_paint].mean():.1f}")

# Keep Unity NM copy synced if cha_strongarm_vh_NM_unity.png exists
if (ASSET_DIR / "cha_strongarm_vh_NM_unity.png").exists():
    # Match cha_strongarm_vh_NM_unity DXT5nm layout (0, G, 0, R) if needed or check existing format
    u_arr = load_rgba("cha_strongarm_vh_NM_unity.png")
    print(f"cha_strongarm_vh_NM_unity.png current means: R={u_arr[:,:,0].mean():.1f} G={u_arr[:,:,1].mean():.1f} B={u_arr[:,:,2].mean():.1f} A={u_arr[:,:,3].mean():.1f}")
