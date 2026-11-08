import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

scene_file = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Vortex_Inspection.unity"
with open(scene_file, 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find Grindor_Official_Reference Transform
# GameObject: Grindor_Official_Reference -> m_Component -> Transform
go_grindor = re.search(r'--- !u!1 &(\d+)\nGameObject:.*?m_Name: Grindor_Official_Reference.*?--- !u!4 &(\d+)\nTransform:', text, re.DOTALL)
if go_grindor:
    print(f"Grindor GO {go_grindor.group(1)}, Transform {go_grindor.group(2)}")
    # Find that Transform's m_LocalPosition
    m = re.search(rf'--- !u!4 &{go_grindor.group(2)}\nTransform:.*?m_LocalPosition: \{{x: ([^,]+), y: ([^,]+), z: ([^\}}]+)\}}', text, re.DOTALL)
    if m:
        print(f"Grindor LocalPosition: x={m.group(1)}, y={m.group(2)}, z={m.group(3)}")

go_vtx = re.search(r'--- !u!1 &(\d+)\nGameObject:.*?m_Name: Vortex_Candidate.*?--- !u!4 &(\d+)\nTransform:', text, re.DOTALL)
if go_vtx:
    print(f"Vortex GO {go_vtx.group(1)}, Transform {go_vtx.group(2)}")
    m = re.search(rf'--- !u!4 &{go_vtx.group(2)}\nTransform:.*?m_LocalPosition: \{{x: ([^,]+), y: ([^,]+), z: ([^\}}]+)\}}', text, re.DOTALL)
    if m:
        print(f"Vortex LocalPosition: x={m.group(1)}, y={m.group(2)}, z={m.group(3)}")
