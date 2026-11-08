import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

scene_file = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Vortex_Inspection.unity"
with open(scene_file, 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find all GameObjects under Grindor_Official_Reference
# In Unity YAML:
# GameObject has m_Name
# Transform has m_GameObject and m_Father

go_names = {} # fileID -> name
for m in re.finditer(r'--- !u!1 &(\d+)\nGameObject:.*?m_Name: ([^\n]+)', text, re.DOTALL):
    go_names[m.group(1)] = m.group(2).strip()

trans_info = {} # fileID -> (go_id, father_id)
for m in re.finditer(r'--- !u!4 &(\d+)\nTransform:.*?m_GameObject: \{fileID: (\d+)\}.*?m_Father: \{fileID: (\d+)\}', text, re.DOTALL):
    trans_info[m.group(1)] = (m.group(2), m.group(3))

# Find Grindor_Official_Reference
grindor_go_id = None
for gid, name in go_names.items():
    if name == "Grindor_Official_Reference":
        grindor_go_id = gid
        break

print(f"Grindor_Official_Reference GO ID: {grindor_go_id}")

# Find all SMRs and their GameObjects
smrs = []
for m in re.finditer(r'--- !u!137 &(\d+)\nSkinnedMeshRenderer:.*?m_GameObject: \{fileID: (\d+)\}.*?m_Enabled: (\d+)', text, re.DOTALL):
    smr_id, go_id, enabled = m.group(1), m.group(2), m.group(3)
    smrs.append((smr_id, go_id, enabled, go_names.get(go_id, "unknown")))

print("\nAll SkinnedMeshRenderers:")
for smr_id, go_id, enabled, name in smrs:
    print(f"SMR {smr_id} on GO {go_id} ({name}), enabled={enabled}")

