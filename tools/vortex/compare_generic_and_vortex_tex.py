import os
import sys
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

tex_dir = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures"

generic_files = [
    "head.jpg", "head_e.jpg", "heads.jpg",
    "chest.jpg", "chest_e.jpg",
    "armup.jpg", "armup_e.jpg",
    "armlo.jpg", "armlo_e.jpg",
    "legs.jpg", "legs_e.jpg",
    "jetpack.jpg"
]

print("Generic texture properties:")
for gf in generic_files:
    p = os.path.join(tex_dir, gf)
    if os.path.exists(p):
        with Image.open(p) as img:
            print(f"  {gf:20s} {img.size} {img.mode} {os.path.getsize(p):>8d} bytes")
    else:
        print(f"  {gf:20s} MISSING")

print("\nVortex specific texture properties:")
for vf in sorted(os.listdir(tex_dir)):
    if "vortex" in vf.lower():
        p = os.path.join(tex_dir, vf)
        with Image.open(p) as img:
            print(f"  {vf:30s} {img.size} {img.mode} {os.path.getsize(p):>8d} bytes")
