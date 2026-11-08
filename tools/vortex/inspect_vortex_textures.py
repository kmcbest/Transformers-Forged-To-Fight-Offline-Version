import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

tex_dir = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures"

vortex_textures = []
for f in os.listdir(tex_dir):
    if "vortex" in f.lower():
        vortex_textures.append(f)

print(f"Total Vortex textures found: {len(vortex_textures)}")
for t in sorted(vortex_textures):
    sz = os.path.getsize(os.path.join(tex_dir, t))
    print(f"  {t:40s} {sz:>10d} bytes")
