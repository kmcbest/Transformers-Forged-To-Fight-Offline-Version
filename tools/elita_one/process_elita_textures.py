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

def process_pack(suffix, out_prefix):
    diffuse_path = TEX_DIR / f"T_CH11_{suffix}_D.png"
    normal_path = TEX_DIR / f"T_CH11_{suffix}_N.png"
    rough_path = TEX_DIR / f"T_CH11_{suffix}_R.png"
    ao_path = TEX_DIR / f"T_CH11_{suffix}_O.png"
    glow_path = TEX_DIR / f"MI_CH11_{suffix}_glow.tga.png"

    # 1. Diffuse with user-requested brightness enhancement
    diff = Image.open(diffuse_path).convert("RGB")
    # Enhance brightness (+15%) and contrast (+10%) for vibrant mobile rendering
    enhancer = ImageEnhance.Brightness(diff)
    diff = enhancer.enhance(1.15)
    enh_c = ImageEnhance.Contrast(diff)
    diff = enh_c.enhance(1.08)
    diff_rgba = diff.convert("RGBA")
    # Resize to 1024x1024 for mobile bundle
    diff_1024 = diff_rgba.resize((1024, 1024), Image.LANCZOS)
    out_diff = OUT_DIR / f"{out_prefix}_diffuse.png"
    diff_1024.save(out_diff)
    print(f"[✓] Saved {out_diff.name} (mean RGB: {np.array(diff_1024)[:,:,:3].mean():.1f})")

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

    # 3.1 Roughness: scale to sleek automotive gloss (matching Arcee's 49.99 mean)
    r_arr = np.clip(r_raw * 0.35, 20, 110).astype(np.uint8)

    # 3.2 AO: lift shadow floor to >= 165 to eliminate black blotches under ambient light
    ao_norm = ao_raw / 255.0
    ao_arr = np.clip(165.0 + (ao_norm ** 0.7) * 90.0, 165, 255).astype(np.uint8)

    # 3.3 Emissive Mask: combine yellow visor, cyan eyes/circuits, and glow map
    visor_mask = (d_raw[:,:,0] > 160) & (d_raw[:,:,1] > 140) & (d_raw[:,:,2] < 90)
    cyan_mask = (d_raw[:,:,0] < 110) & (d_raw[:,:,1] > 130) & (d_raw[:,:,2] > 150)
    if glow_path.is_file():
        g_raw = np.array(Image.open(glow_path).convert("RGB"))
        glow_mask = np.any(g_raw > 40, axis=-1)
    else:
        glow_mask = np.zeros(d_raw.shape[:2], dtype=bool)

    combined_mask = visor_mask | cyan_mask | glow_mask
    from scipy.ndimage import binary_dilation
    dilated_mask = binary_dilation(combined_mask, structure=np.ones((3, 3)))

    e_arr = np.zeros_like(r_arr)
    e_arr[dilated_mask] = 255

    # Pack RAOE into 1024x1024 for high-definition mobile rendering
    raoe_2048 = np.stack([r_arr, ao_arr, e_arr], axis=-1)
    raoe_img = Image.fromarray(raoe_2048, "RGB").resize((1024, 1024), Image.BILINEAR)
    out_raoe = OUT_DIR / f"{out_prefix}_raoe.png"
    raoe_img.save(out_raoe)
    print(f"[✓] Saved {out_raoe.name} (R_mean={r_arr.mean():.1f}, AO_min={ao_arr.min()}, AO_mean={ao_arr.mean():.1f}, E_pixels={np.count_nonzero(e_arr)})")

print("Processing Elita One Textures...")
process_pack("00", "elita_main")
process_pack("01", "elita_vh")
print("Done!")
