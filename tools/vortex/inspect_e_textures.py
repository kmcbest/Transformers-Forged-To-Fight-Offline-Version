import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

tex_dir = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures"

all_files = os.listdir(tex_dir)
print(f"Total files in textures: {len(all_files)}")
print("\nFiles with '_e' in name:")
for f in sorted(all_files):
    if "_e" in f.lower():
        print(" ", f)
