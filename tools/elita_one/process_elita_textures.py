# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
from PIL import Image, ImageEnhance
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
TEX_DIR = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "textures"
OUT_DIR = ROOT / "tools" / "elita_one" / "processed_textures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def paint_autobot_eyes(diff_np, raoe_np):
    """
    Paints perfectly symmetric glowing Autobot eyes with dark charcoal eyeliner framing
    onto the 1024x1024 diffuse and RAOE textures.
    - Left Eye: X in [81, 105], Y in [540, 549]
    - Right Eye: X in [123, 147], Y in [540, 549]
    """
    # 1. Clean eye socket background to charcoal grey [45, 45, 48]
    for y in range(536, 554):
        for x in range(75, 153):
            diff_np[y, x, :3] = [45, 45, 48]
            raoe_np[y, x, 2] = 0

    def draw_styled_eye(x1, x2, y1, y2):
        # Eyeliner border (charcoal black [18, 18, 20])
        for y in range(y1 - 2, y2 + 3):
            for x in range(x1 - 2, x2 + 3):
                diff_np[y, x, :3] = [18, 18, 20]
                
        # Eye fill: superellipse rounded corners
        w = x2 - x1 + 1
        h = y2 - y1 + 1
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        rx = w / 2.0
        ry = h / 2.0
        
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                nx = abs((x - cx) / rx)
                ny = abs((y - cy) / ry)
                val = (nx ** 4) + (ny ** 4)
                if val <= 1.0:
                    # Radial glow: core is bright white-cyan [180, 255, 255], outer is electric cyan [10, 230, 255]
                    dist = np.sqrt(nx**2 + ny**2)
                    r = int(180 * max(0, 1.0 - dist) + 10 * min(1.0, dist))
                    g = int(255 * max(0, 1.0 - dist * 0.1) + 230 * min(1.0, dist * 0.1))
                    b = 255
                    diff_np[y, x, :3] = [r, g, b]
                    raoe_np[y, x, 2] = 255
                elif val <= 1.3:
                    # Antialiased bloom edge in emissive mask
                    raoe_np[y, x, 2] = 160

    draw_styled_eye(81, 105, 540, 549)
    draw_styled_eye(123, 147, 540, 549)

def process_pack(suffix, out_prefix):
    diffuse_path = TEX_DIR / f"T_CH11_{suffix}_D.png"
    normal_path = TEX_DIR / f"T_CH11_{suffix}_N.png"
    rough_path = TEX_DIR / f"T_CH11_{suffix}_R.png"
    ao_path = TEX_DIR / f"T_CH11_{suffix}_O.png"
    glow_path = TEX_DIR / f"MI_CH11_{suffix}_glow.tga.png"

    # 1. Diffuse with brightness enhancement
    diff = Image.open(diffuse_path).convert("RGB")
    enhancer = ImageEnhance.Brightness(diff)
    diff = enhancer.enhance(1.15)
    enh_c = ImageEnhance.Contrast(diff)
    diff = enh_c.enhance(1.08)
    diff_rgba = diff.convert("RGBA")
    diff_1024 = diff_rgba.resize((1024, 1024), Image.LANCZOS)
    diff_np = np.array(diff_1024)

    # 2. Normal map
    norm = Image.open(normal_path).convert("RGBA")
    norm_resized = norm.resize((1024, 1024), Image.LANCZOS)
    out_norm = OUT_DIR / f"{out_prefix}_normal.png"
    norm_resized.save(out_norm)
    print(f"[✓] Saved {out_norm.name}")

    # 3. RAOE packing: R=Roughness (~50), G=Lifted AO (>=165), B=Emissive Mask (255)
    d_raw = np.array(Image.open(diffuse_path).convert("RGB"))
    r_raw = np.array(Image.open(rough_path).convert("L"), dtype=np.float32)
    ao_raw = np.array(Image.open(ao_path).convert("L"), dtype=np.float32)

    # 3.1 Roughness: scale to sleek automotive gloss
    r_arr = np.clip(r_raw * 0.35, 20, 110).astype(np.uint8)

    # 3.2 AO: lift shadow floor to >= 165
    ao_norm = ao_raw / 255.0
    ao_arr = np.clip(165.0 + (ao_norm ** 0.7) * 90.0, 165, 255).astype(np.uint8)

    # 3.3 Emissive Mask: yellow visor and glow map
    visor_mask = (d_raw[:,:,0] > 160) & (d_raw[:,:,1] > 140) & (d_raw[:,:,2] < 90)
    if glow_path.is_file():
        g_raw = np.array(Image.open(glow_path).convert("RGB"))
        glow_mask = np.any(g_raw > 40, axis=-1)
    else:
        glow_mask = np.zeros(d_raw.shape[:2], dtype=bool)

    combined_mask = visor_mask | glow_mask
    from scipy.ndimage import binary_dilation
    dilated_mask = binary_dilation(combined_mask, structure=np.ones((3, 3)))

    e_arr = np.zeros_like(r_arr)
    e_arr[dilated_mask] = 255

    # Pack RAOE into 1024x1024
    raoe_2048 = np.stack([r_arr, ao_arr, e_arr], axis=-1)
    raoe_img = Image.fromarray(raoe_2048, "RGB").resize((1024, 1024), Image.BILINEAR)
    raoe_np = np.array(raoe_img)

    # If processing main robot body, paint the glowing Autobot eyes on both Diffuse and RAOE!
    if suffix == "00":
        paint_autobot_eyes(diff_np, raoe_np)

    # Save final Diffuse and RAOE
    final_diff = Image.fromarray(diff_np)
    out_diff = OUT_DIR / f"{out_prefix}_diffuse.png"
    final_diff.save(out_diff)
    print(f"[✓] Saved {out_diff.name} (mean RGB: {diff_np[:,:,:3].mean():.1f})")

    final_raoe = Image.fromarray(raoe_np)
    out_raoe = OUT_DIR / f"{out_prefix}_raoe.png"
    final_raoe.save(out_raoe)
    print(f"[✓] Saved {out_raoe.name} (R_mean={r_arr.mean():.1f}, AO_min={ao_arr.min()}, AO_mean={ao_arr.mean():.1f}, E_pixels={np.count_nonzero(raoe_np[:,:,2])})")

print("Processing Elita One Textures with Symmetric Luminous Autobot Eyes...")
process_pack("00", "elita_main")
process_pack("01", "elita_vh")
print("Done!")
