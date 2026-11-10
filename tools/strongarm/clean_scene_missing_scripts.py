import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import shutil
import re

scene_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Strongarm_Inspection.unity"
bak_path = scene_path + ".bak"
shutil.copyfile(scene_path, bak_path)

with open(scene_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Find all missing IDs
docs = text.split("--- !u!")
header = docs[0]
blocks = docs[1:]

missing_ids = set()
for b in blocks:
    if b.startswith("114 &"):
        m = re.search(r'm_Script: \{fileID: -?\d+, guid: 0{32}', b)
        if m:
            block_id = b.split("\n")[0].split("&")[1].strip()
            missing_ids.add(block_id)

print(f"Identified {len(missing_ids)} missing MonoBehaviours to strip.")

# 2. Filter out missing blocks
kept_blocks = []
for b in blocks:
    first_line = b.split("\n")[0]
    if "&" in first_line:
        block_id = first_line.split("&")[1].strip()
        if block_id in missing_ids:
            continue
    kept_blocks.append(b)

# 3. Clean GameObject component references
cleaned_blocks = []
for b in kept_blocks:
    if b.startswith("1 &"): # GameObject block
        # remove component references to missing_ids
        for mid in missing_ids:
            pattern = re.compile(rf'  - component: \{{fileID: {mid}\}}\n')
            b = pattern.sub('', b)
    cleaned_blocks.append(b)

new_text = header + "--- !u!" + "--- !u!".join(cleaned_blocks)

with open(scene_path, 'w', encoding='utf-8') as f:
    f.write(new_text)

print(f"[✓] Successfully stripped all {len(missing_ids)} missing MonoBehaviour components from Strongarm_Inspection.unity!")
