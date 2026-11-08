import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

scene_file = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Scenes\Vortex_Inspection.unity"
with open(scene_file, 'r', encoding='utf-8') as f:
    text = f.read()

import re

go_names = {}
for m in re.finditer(r'--- !u!1 &(\d+)\nGameObject:.*?m_Name: ([^\n]+)', text, re.DOTALL):
    go_names[m.group(1)] = m.group(2).strip()

# Map trans_id -> (go_id, father_trans_id)
# And go_id -> trans_id
trans_to_go = {}
trans_father = {}
go_to_trans = {}
for m in re.finditer(r'--- !u!4 &(\d+)\nTransform:.*?m_GameObject: \{fileID: (\d+)\}.*?m_Father: \{fileID: (\d+)\}', text, re.DOTALL):
    t_id, g_id, f_id = m.group(1), m.group(2), m.group(3)
    trans_to_go[t_id] = g_id
    trans_father[t_id] = f_id
    go_to_trans[g_id] = t_id

def get_root_name(go_id):
    curr_t = go_to_trans.get(go_id)
    while curr_t and curr_t != '0':
        father_t = trans_father.get(curr_t, '0')
        if father_t == '0':
            curr_go = trans_to_go.get(curr_t)
            return go_names.get(curr_go, "root")
        curr_t = father_t
    return "unknown"

for m in re.finditer(r'--- !u!137 &(\d+)\nSkinnedMeshRenderer:.*?m_GameObject: \{fileID: (\d+)\}.*?m_Enabled: (\d+)', text, re.DOTALL):
    smr_id, go_id, enabled = m.group(1), m.group(2), m.group(3)
    root = get_root_name(go_id)
    print(f"SMR {smr_id} on GO '{go_names.get(go_id)}' (Root: {root}), enabled={enabled}")

