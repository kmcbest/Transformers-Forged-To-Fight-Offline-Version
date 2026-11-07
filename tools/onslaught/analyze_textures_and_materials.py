import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path

tex_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures")

files = list(tex_dir.glob("*"))
print(f"Total files in textures dir: {len(files)}")

categories = {
    "onslaught": [],
    "wep": [],
    "blastoff": [],
    "brawl": [],
    "swindle": [],
    "vortex": [],
    "bruticus": [],
    "other": []
}

for f in sorted(files, key=lambda x: x.name):
    name_l = f.name.lower()
    matched = False
    for k in ["onslaught", "wep", "blastoff", "brawl", "swindle", "vortex", "bruticus"]:
        if k in name_l:
            categories[k].append(f.name)
            matched = True
            break
    if not matched:
        categories["other"].append(f.name)

for k, flist in categories.items():
    print(f"\n--- {k.upper()} ({len(flist)}) ---")
    for fname in flist:
        print(f"  {fname}")
