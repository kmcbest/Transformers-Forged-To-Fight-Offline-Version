import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

SRC_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\blitzwing_extracted\rar")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\Textures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEX_CONFIGS = [
    ("Body", "Body.jpg", "Body_Highlights.jpg", None),
    ("Legs", "Legs.jpg", "Legs_Highlights.jpg", None),
    ("Hands", "Hands.jpg", "Hands_Highlights.jpg", None),
    ("Tank", "Body_Alt_Tank.jpg", "Body_Alt_Tank_Highlights.jpg", None),
    ("Jet", "Body_Alt_Jet.jpg", "Body_Alt_Jet_Highlights.jpg", None),
    ("Treads", "Body_Alt_Treads.jpg", "Treads_Highlights.jpg", None),
]

def clean_decel_image(base_img, hl_img):
    arr = np.array(base_img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    
    if hl_img:
        hl = np.array(hl_img.convert("L").resize((w, h)), dtype=np.float32) / 255.0
    else:
        hl = np.zeros((h, w), dtype=np.float32)
        
    # Use MedianFilter(15) to get local flat color tone
    med_im = base_img.convert("RGB").filter(ImageFilter.MedianFilter(size=15))
    med = np.array(med_im, dtype=np.float32)
    diff = np.linalg.norm(arr - med, axis=2)
    
    # Identify painted cel streaks: medium-contrast deviation or highlight mask
    # Preserves fine decals/stripes/insignia (high contrast > 55 or distinct hue)
    mask_streak = ((diff > 3.0) & (diff < 45.0)) | (hl > 0.30)
    
    # Smooth blend toward local median on painted streaks
    alpha = np.clip(mask_streak.astype(np.float32) * 0.82, 0.0, 0.88)[:, :, None]
    out = arr * (1.0 - alpha) + med * alpha
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def build_normal_map(diff_img, strength=2.2):
    gray = diff_img.convert("L")
    arr = np.array(gray, dtype=np.float32)
    gy, gx = np.gradient(arr)
    
    nx = -gx * strength
    ny = -gy * strength
    nz = np.ones_like(nx) * 255.0
    
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm
    
    r = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    g = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    b = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")

def build_raoe_map(diff_img, hl_img, is_treads=False):
    w, h = diff_img.size
    gray_arr = np.array(diff_img.convert("L"), dtype=np.float32)
    
    if hl_img:
        hl_arr = np.array(hl_img.convert("L").resize((w, h)), dtype=np.float32) / 255.0
    else:
        hl_arr = np.zeros((h, w), dtype=np.float32)
        
    if is_treads:
        roughness = np.ones((h, w), dtype=np.float32) * 0.65
        metallic = np.ones((h, w), dtype=np.float32) * 0.35
    else:
        # Purple metallic armor: Roughness ~0.32, Metallic ~0.78
        roughness = np.clip(0.36 - hl_arr * 0.12, 0.20, 0.55)
        metallic = np.clip(0.76 + hl_arr * 0.10, 0.60, 0.90)
        
    # Cavity AO from luminance
    ao = np.clip(gray_arr / 255.0 * 0.35 + 0.65, 0.30, 1.0)
    # Emission (blank except yellow/red lights if any)
    emissive = np.zeros((h, w), dtype=np.float32)
    
    r = np.clip(roughness * 255.0, 0, 255).astype(np.uint8)
    g = np.clip(ao * 255.0, 0, 255).astype(np.uint8)
    b = np.clip(metallic * 255.0, 0, 255).astype(np.uint8)
    a = np.clip(emissive * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([r, g, b, a], axis=-1), mode="RGBA")

print("=== Generating De-cel'd PBR Texture Sets for Blitzwing ===")
for prefix, base_name, hl_name, _ in TEX_CONFIGS:
    base_file = SRC_DIR / base_name
    hl_file = SRC_DIR / hl_name if hl_name else None
    
    if not base_file.exists():
        print(f"[-] Missing: {base_name}")
        continue
        
    base_img = Image.open(base_file)
    hl_img = Image.open(hl_file) if (hl_file and hl_file.exists()) else None
    
    is_treads = (prefix == "Treads")
    clean_diff = clean_decel_image(base_img, hl_img)
    clean_diff.save(OUT_DIR / f"{prefix}_Diffuse.png")
    
    nm = build_normal_map(clean_diff)
    nm.save(OUT_DIR / f"{prefix}_Normal.png")
    
    raoe = build_raoe_map(clean_diff, hl_img, is_treads=is_treads)
    raoe.save(OUT_DIR / f"{prefix}_RAOE.png")
    
    print(f"[✓] {prefix:8s}: {base_img.size} -> Diffuse, Normal, RAOE generated.")

print("=== PBR Textures Generation Completed! ===")
