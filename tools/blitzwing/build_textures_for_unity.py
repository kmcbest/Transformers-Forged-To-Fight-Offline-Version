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

def process_texture_set(prefix, base_file, high_file, line_file=None):
    base_path = SRC_DIR / base_file
    high_path = SRC_DIR / high_file if high_file else None
    
    if not base_path.exists():
        print(f"Skipping {prefix}: {base_file} not found")
        return
        
    diff = Image.open(base_path).convert("RGBA")
    w, h = diff.size
    
    # 1. Save Diffuse PNG
    diff_out = OUT_DIR / f"{prefix}_Diffuse.png"
    diff.save(diff_out)
    
    # 2. Build Normal Map (OpenGL Tangent Normal)
    # R=X (128), G=Y (128), B=Z (255) with edge relief from line_file / grayscale
    if line_file and (SRC_DIR / line_file).exists():
        gray = Image.open(SRC_DIR / line_file).convert("L")
    else:
        gray = diff.convert("L")
    
    # Simple Sobel / gradient bump
    gray_arr = np.array(gray, dtype=np.float32)
    # Gradients
    gy, gx = np.gradient(gray_arr)
    # Scale bump strength
    strength = 1.5
    nx = -gx * strength
    ny = -gy * strength
    nz = np.ones_like(nx) * 255.0
    
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm
    
    r_chan = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    g_chan = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    b_chan = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    
    nm_img = Image.fromarray(np.stack([r_chan, g_chan, b_chan], axis=-1), mode="RGB")
    nm_out = OUT_DIR / f"{prefix}_Normal.png"
    nm_img.save(nm_out)
    
    # 3. Build RAOE Map (R: Roughness, G: AO, B: Metallic, A: Emissive)
    if high_path and high_path.exists():
        h_arr = np.array(Image.open(high_path).convert("L"), dtype=np.float32) / 255.0
    else:
        h_arr = np.ones((h, w), dtype=np.float32) * 0.5
        
    # Roughness: inverted highlight (smoother where highlighted)
    roughness = np.clip((1.0 - h_arr * 0.6) * 255.0, 50, 240).astype(np.uint8)
    # AO: ~0.90 with subtle cavity shadows
    ao = np.clip((gray_arr / 255.0 * 0.3 + 0.7) * 255.0, 100, 255).astype(np.uint8)
    # Metallic: ~0.65 for mechanical armor
    metallic = np.clip((h_arr * 0.5 + 0.4) * 255.0, 40, 220).astype(np.uint8)
    # Emissive: Default 0
    emissive = np.zeros((h, w), dtype=np.uint8)
    
    raoe_img = Image.fromarray(np.stack([roughness, ao, metallic, emissive], axis=-1), mode="RGBA")
    raoe_out = OUT_DIR / f"{prefix}_RAOE.png"
    raoe_img.save(raoe_out)
    
    print(f"[✓] Generated PBR set for '{prefix}': {diff_out.name}, {nm_out.name}, {raoe_out.name}")

# Process all sets
process_texture_set("Body", "Body.jpg", "Body_Highlights.jpg", "Body_2.jpg")
process_texture_set("Legs", "Legs.jpg", "Legs_Highlights.jpg", "Legs_2.jpg")
process_texture_set("Hands", "Hands.jpg", "Hands_Highlights.jpg", "Hands_2.jpg")
process_texture_set("Tank", "Body_Alt_Tank.jpg", "Body_Alt_Tank_Highlights.jpg", "Body_Alt_Tank_2.jpg")
process_texture_set("Treads", "Body_Alt_Treads.jpg", "Treads_Highlights.jpg", "Body_Alt_Treads_2.jpg")
process_texture_set("Jet", "Body_Alt_Jet.jpg", "Body_Alt_Jet_Highlights.jpg", "Body_Alt_Jet_2.jpg")

print("=== ALL TEXTURES PROCESSED SUCCESSFULLY ===")
