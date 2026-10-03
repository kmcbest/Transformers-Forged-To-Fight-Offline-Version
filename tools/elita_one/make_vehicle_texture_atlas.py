import sys
from PIL import Image
from pathlib import Path
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_DIR = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "textures"
OUT_TEX_DIR = ROOT / "tools" / "elita_one" / "processed_textures"
OUT_TEX_DIR.mkdir(parents=True, exist_ok=True)

print("=== [1/2] Generating Vehicle Texture Atlas ===")
# 1. Diffuse Atlas (2048x2048): Top = VH00, Bottom = VH01
d00 = Image.open(TEX_DIR / "T_VH11_00_D.png").convert("RGBA")
d01 = Image.open(TEX_DIR / "T_VH11_01_D.png").convert("RGBA")

d00_half = d00.resize((2048, 1024), Image.LANCZOS)
d01_half = d01.resize((2048, 1024), Image.LANCZOS)

atlas_diff = Image.new("RGBA", (2048, 2048))
atlas_diff.paste(d00_half, (0, 0))
atlas_diff.paste(d01_half, (0, 1024))

out_diff_path = OUT_TEX_DIR / "elita_veh_atlas_diffuse.png"
atlas_diff.save(out_diff_path)
print(f"[✓] Saved diffuse atlas: {out_diff_path.name}")

# 2. Normal Atlas (2048x2048): Top = VH00, Bottom = VH01
n00 = Image.open(TEX_DIR / "T_VH11_00_N.png").convert("RGBA").resize((2048, 1024), Image.LANCZOS)
n01 = Image.open(TEX_DIR / "T_VH11_01_N.png").convert("RGBA").resize((2048, 1024), Image.LANCZOS)
atlas_norm = Image.new("RGBA", (2048, 2048))
atlas_norm.paste(n00, (0, 0))
atlas_norm.paste(n01, (0, 1024))
out_norm_path = OUT_TEX_DIR / "elita_veh_atlas_normal.png"
atlas_norm.save(out_norm_path)
print(f"[✓] Saved normal atlas: {out_norm_path.name}")

# 3. RAOE Atlas (1024x1024 for mobile performance):
def make_raoe_half(suffix):
    r_img = Image.open(TEX_DIR / f"T_VH11_{suffix}_R.png").convert("L").resize((1024, 512), Image.BILINEAR)
    ao_img = Image.open(TEX_DIR / f"T_VH11_{suffix}_O.png").convert("L").resize((1024, 512), Image.BILINEAR)
    glow_p = TEX_DIR / f"mat_vh{int(suffix)}_glow.tga.png"
    if glow_p.is_file():
        e_img = Image.open(glow_p).convert("L").resize((1024, 512), Image.BILINEAR)
        e_arr = np.clip(np.array(e_img, dtype=np.float32) * 2.0, 0, 255).astype(np.uint8)
    else:
        e_arr = np.zeros((512, 1024), dtype=np.uint8)
    r_arr = np.clip(np.array(r_img, dtype=np.float32) * 0.85, 20, 240).astype(np.uint8)
    ao_arr = np.array(ao_img, dtype=np.uint8)
    return np.stack([r_arr, ao_arr, e_arr], axis=-1)

raoe00 = make_raoe_half("00")
raoe01 = make_raoe_half("01")
atlas_raoe_arr = np.concatenate([raoe00, raoe01], axis=0) # 1024 x 1024 x 3
atlas_raoe = Image.fromarray(atlas_raoe_arr, "RGB")
out_raoe_path = OUT_TEX_DIR / "elita_veh_atlas_raoe.png"
atlas_raoe.save(out_raoe_path)
print(f"[✓] Saved RAOE atlas: {out_raoe_path.name}")
