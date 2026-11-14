import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import re

scene_path = Path(r"E:\Agent\TFTF-blender\stage_project\Assets\Scenes\Karnak_Combiners_Stage.unity")
content = scene_path.read_text(encoding="utf-8")

# Let's find Volcanicus_Colossus Transform
# Find GameObject: m_Name: Volcanicus_Colossus
# Then its Transform
lines = content.splitlines()

volc_go_id = None
vic_go_id = None
for i, l in enumerate(lines):
    if "m_Name: Volcanicus_Colossus" in l:
        volc_go_id = lines[i-5].split("&")[1].strip()
    elif "m_Name: Victorion_Colossus" in l:
        vic_go_id = lines[i-5].split("&")[1].strip()

print(f"Volcanicus GO ID: {volc_go_id}, Victorion GO ID: {vic_go_id}")

# Find transforms referencing these GO IDs
for i, l in enumerate(lines):
    if volc_go_id and f"m_GameObject: {{fileID: {volc_go_id}}}" in l:
        # Update lines around i
        for j in range(i-5, i+15):
            if "m_LocalRotation:" in lines[j]:
                lines[j] = "  m_LocalRotation: {x: 0, y: 0.91976, z: 0, w: 0.39249}"
            elif "m_LocalPosition:" in lines[j]:
                lines[j] = "  m_LocalPosition: {x: -48, y: 1.5, z: 46}"
            elif "m_LocalScale:" in lines[j]:
                lines[j] = "  m_LocalScale: {x: 600, y: 600, z: 600}"
    elif vic_go_id and f"m_GameObject: {{fileID: {vic_go_id}}}" in l:
        for j in range(i-5, i+15):
            if "m_LocalRotation:" in lines[j]:
                lines[j] = "  m_LocalRotation: {x: 0, y: -0.92388, z: 0, w: 0.38268}"
            elif "m_LocalPosition:" in lines[j]:
                lines[j] = "  m_LocalPosition: {x: 46, y: 4.13, z: 46}"
            elif "m_LocalScale:" in lines[j]:
                lines[j] = "  m_LocalScale: {x: 130, y: 130, z: 130}"

scene_path.write_text("\n".join(lines), encoding="utf-8")
print("[✓] Updated Karnak_Combiners_Stage.unity with positions ① and ②!")
