import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "Textures"
OUT_TEX_DIR = ROOT / "tools" / "blitzwing" / "atlased_textures"
OUT_TEX_DIR.mkdir(parents=True, exist_ok=True)

# 1. Build Robot Atlas (4096 x 4096)
def build_robot_atlas(img_type, mode, default_color):
    atlas = Image.new(mode, (4096, 4096), default_color)
    body_img = Image.open(TEX_DIR / f"Body_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    hands_img = Image.open(TEX_DIR / f"Hands_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    legs_img = Image.open(TEX_DIR / f"Legs_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)

    atlas.paste(body_img, (0, 0))        # Top-Left: Body (U: [0..0.5], V: [0.5..1.0])
    atlas.paste(hands_img, (2048, 0))    # Top-Right: Hands (U: [0.5..1.0], V: [0.5..1.0])
    atlas.paste(legs_img, (0, 2048))     # Bottom-Left: Legs (U: [0..0.5], V: [0..0.5])
    atlas.paste(body_img, (2048, 2048))  # Bottom-Right: Spare Body

    out_path = OUT_TEX_DIR / f"cha_blitzwing_main_{img_type}.png"
    atlas.save(out_path)
    print(f"[✓] Saved Robot Atlas {out_path.name}: {atlas.size}, mode={atlas.mode}")

# 2. Build Vehicle Atlas (4096 x 4096)
# Top-Left: Tank (U: [0..0.5], V: [0.5..1.0])
# Top-Right: Jet (U: [0.5..1.0], V: [0.5..1.0])
# Bottom-Left: Treads (U: [0..0.5], V: [0..0.5])
# Bottom-Right: Body (U: [0.5..1.0], V: [0..0.5])
def build_vehicle_atlas(img_type, mode, default_color):
    atlas = Image.new(mode, (4096, 4096), default_color)
    tank_img = Image.open(TEX_DIR / f"Tank_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    jet_img = Image.open(TEX_DIR / f"Jet_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    treads_img = Image.open(TEX_DIR / f"Treads_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    body_img = Image.open(TEX_DIR / f"Body_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)

    atlas.paste(tank_img, (0, 0))        # Top-Left: Tank
    atlas.paste(jet_img, (2048, 0))      # Top-Right: Jet
    atlas.paste(treads_img, (0, 2048))   # Bottom-Left: Treads
    atlas.paste(body_img, (2048, 2048))  # Bottom-Right: Body

    out_path = OUT_TEX_DIR / f"cha_blitzwing_tform_misc_{img_type}.png"
    atlas.save(out_path)
    print(f"[✓] Saved Vehicle Atlas {out_path.name}: {atlas.size}, mode={atlas.mode}")

print("=== Generating Robot & Vehicle Atlases ===")
for it, mode, def_col in [
    ("Diffuse", "RGB", (0, 0, 0)),
    ("Normal", "RGB", (128, 128, 255)),
    ("RAOE", "RGBA", (128, 255, 128, 0)),
]:
    build_robot_atlas(it, mode, def_col)
    build_vehicle_atlas(it, mode, def_col)
