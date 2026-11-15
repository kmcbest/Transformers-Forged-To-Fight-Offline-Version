#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_atlased_pbr_textures.py
Strict adherence to THIRD_PARTY_3D_MODEL_PIPELINE.md section 11.9 & 11.10:
  1. RAOE:
     - R = Roughness (180..215 satin)
     - G = Ambient Occlusion (165..255)
     - B = Emissive (MUST BE STRICTLY 0 for all non-glowing surfaces!)
     - A = 0
  2. Normal:
     - R = Normal X (tangent space)
     - G = Normal Y (tangent space)
     - B = Metallic (0 for painted purple/yellow/white armor, 95 for neutral grey metal joints/treads)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "Textures"
OUT_TEX_DIR = ROOT / "tools" / "blitzwing" / "atlased_textures"
OUT_TEX_DIR.mkdir(parents=True, exist_ok=True)

PARTS = ["Body", "Legs", "Hands", "Tank", "Jet", "Treads"]

def process_part(name: str):
    diff_p = TEX_DIR / f"{name}_Diffuse.png"
    norm_p = TEX_DIR / f"{name}_Normal.png"
    raoe_p = TEX_DIR / f"{name}_RAOE.png"

    diff_img = Image.open(diff_p).convert("RGB")
    norm_img = Image.open(norm_p).convert("RGB")
    raoe_img = Image.open(raoe_p).convert("RGBA")

    diff_arr = np.array(diff_img, dtype=np.float32)
    norm_arr = np.array(norm_img, dtype=np.uint8)
    raoe_arr = np.array(raoe_img, dtype=np.uint8)

    h, w = diff_arr.shape[:2]

    # 1. Calculate Metallic Mask from Diffuse saturation
    # Colored purple/yellow/red: high saturation -> Metallic = 0
    # Neutral grey skeleton/gun/treads: low saturation (< 0.22) -> Metallic = 95
    mx = np.max(diff_arr, axis=2)
    mn = np.min(diff_arr, axis=2)
    diff = mx - mn
    sat = np.zeros_like(mx)
    mask = mx > 10
    sat[mask] = diff[mask] / mx[mask]

    if name == "Treads":
        metallic = np.ones((h, w), dtype=np.uint8) * 95
    else:
        is_metal = (sat < 0.22) & (mx > 25) & (mx < 190)
        metallic = np.where(is_metal, 95, 0).astype(np.uint8)

    # 2. Put Metallic into Normal Channel B (Kabam Normal spec)
    norm_arr[:, :, 2] = metallic
    new_norm_img = Image.fromarray(norm_arr, mode="RGB")
    new_norm_img.save(TEX_DIR / f"{name}_Normal.png")

    # 3. Fix RAOE:
    # R: Roughness (180..215)
    # G: AO (from existing G channel)
    # B: EMISSIVE (STRICTLY 0! NO METALLIC IN B!)
    # A: 0
    new_raoe_arr = np.zeros((h, w, 4), dtype=np.uint8)
    # Keep existing R or set to satin ~185
    new_raoe_arr[:, :, 0] = np.clip(raoe_arr[:, :, 0].astype(np.float32) * 0.5 + 130, 175, 215).astype(np.uint8)
    new_raoe_arr[:, :, 1] = raoe_arr[:, :, 1]  # AO
    new_raoe_arr[:, :, 2] = 0                  # Emissive = 0! (Eliminating White Supernova!)
    new_raoe_arr[:, :, 3] = 0                  # Alpha = 0

    new_raoe_img = Image.fromarray(new_raoe_arr, mode="RGBA")
    new_raoe_img.save(TEX_DIR / f"{name}_RAOE.png")

    print(f"[✓] Processed {name:8s}: Normal.B = Metallic (mean={np.mean(metallic):.1f}), RAOE.B = 0 (Emissive=0)")

for part in PARTS:
    process_part(part)

# 4. Rebuild Atlases
print("\n=== Rebuilding Atlases ===")
# Robot Atlas (4096 x 4096)
for img_type, mode, default_color in [
    ("Diffuse", "RGB", (0, 0, 0)),
    ("Normal", "RGB", (128, 128, 0)),
    ("RAOE", "RGBA", (185, 255, 0, 0)),
]:
    atlas = Image.new(mode, (4096, 4096), default_color)
    body_img = Image.open(TEX_DIR / f"Body_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    hands_img = Image.open(TEX_DIR / f"Hands_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    legs_img = Image.open(TEX_DIR / f"Legs_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)

    atlas.paste(body_img, (0, 0))        # Top-Left: Body
    atlas.paste(hands_img, (2048, 0))    # Top-Right: Hands
    atlas.paste(legs_img, (0, 2048))     # Bottom-Left: Legs
    atlas.paste(body_img, (2048, 2048))  # Bottom-Right: Spare Body

    out_p = OUT_TEX_DIR / f"cha_blitzwing_main_{img_type}.png"
    atlas.save(out_p)
    print(f"  [Robot Atlas] {out_p.name}: size={atlas.size}, mode={atlas.mode}")

# Vehicle Atlas (4096 x 4096)
for img_type, mode, default_color in [
    ("Diffuse", "RGB", (0, 0, 0)),
    ("Normal", "RGB", (128, 128, 0)),
    ("RAOE", "RGBA", (185, 255, 0, 0)),
]:
    atlas = Image.new(mode, (4096, 4096), default_color)
    tank_img = Image.open(TEX_DIR / f"Tank_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    jet_img = Image.open(TEX_DIR / f"Jet_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    treads_img = Image.open(TEX_DIR / f"Treads_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)
    body_img = Image.open(TEX_DIR / f"Body_{img_type}.png").convert(mode).resize((2048, 2048), Image.LANCZOS)

    atlas.paste(tank_img, (0, 0))        # Top-Left: Tank
    atlas.paste(jet_img, (2048, 0))      # Top-Right: Jet
    atlas.paste(treads_img, (0, 2048))   # Bottom-Left: Treads
    atlas.paste(body_img, (2048, 2048))  # Bottom-Right: Body

    out_p = OUT_TEX_DIR / f"cha_blitzwing_tform_misc_{img_type}.png"
    atlas.save(out_p)
    print(f"  [Vehicle Atlas] {out_p.name}: size={atlas.size}, mode={atlas.mode}")

print("\n=== Atlased Textures Rebuilt OK ===")
