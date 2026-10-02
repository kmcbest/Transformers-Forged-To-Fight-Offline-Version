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

    # 3. RAOE packing: R=Roughness, G=AO, B=Emissive
    r_img = Image.open(rough_path).convert("L").resize((512, 512), Image.BILINEAR)
    ao_img = Image.open(ao_path).convert("L").resize((512, 512), Image.BILINEAR)
    
    r_arr = np.array(r_img, dtype=np.float32)
    # Target roughness ~115-135 for rich satin metal
    r_arr = np.clip(r_arr * 0.85, 20, 240).astype(np.uint8)

    ao_arr = np.array(ao_img, dtype=np.uint8)

    if glow_path.is_file():
        g_img = Image.open(glow_path).convert("L").resize((512, 512), Image.BILINEAR)
        e_arr = np.array(g_img, dtype=np.uint8)
        # Boost glow channel visibility
        e_arr = np.clip(e_arr * 2.0, 0, 255).astype(np.uint8)
    else:
        e_arr = np.zeros((512, 512), dtype=np.uint8)

    raoe_arr = np.stack([r_arr, ao_arr, e_arr], axis=-1)
    raoe_img = Image.fromarray(raoe_arr, "RGB")
    out_raoe = OUT_DIR / f"{out_prefix}_raoe.png"
    raoe_img.save(out_raoe)
    print(f"[✓] Saved {out_raoe.name} (R_mean={r_arr.mean():.1f}, AO_mean={ao_arr.mean():.1f}, E_max={e_arr.max()})")

print("Processing Elita One Textures...")
process_pack("00", "elita_main")
process_pack("01", "elita_vh")
print("Done!")
