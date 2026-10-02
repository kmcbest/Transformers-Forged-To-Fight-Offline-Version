import json
import UnityPy

bpath = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bpath)

tr_to_go = {}
go_to_name = {}
tr_dict = {}

for obj in env.objects:
    if obj.type.name == 'GameObject':
        go = obj.read_typetree()
        go_to_name[obj.path_id] = go.get('m_Name')
    elif obj.type.name == 'Transform':
        tr = obj.read_typetree()
        tr_dict[obj.path_id] = tr
        tr_to_go[obj.path_id] = tr.get('m_GameObject', {}).get('m_PathID')

hierarchy = {}

for tr_id, tr in tr_dict.items():
    go_id = tr_to_go.get(tr_id)
    name = go_to_name.get(go_id)
    parent_tr_id = tr.get('m_Father', {}).get('m_PathID')
    parent_go_id = tr_to_go.get(parent_tr_id)
    parent_name = go_to_name.get(parent_go_id)
    if name:
        hierarchy[name] = parent_name

out_path = r"E:\Agent\TFTF-blender\tools\elita_one\arcee_bone_hierarchy.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(hierarchy, f, indent=2)

print(f"Saved hierarchy of {len(hierarchy)} nodes to {out_path}")
# Print the chain for Hips
for b in ["Hips", "Spine", "Spine1", "Neck", "Head", "LeftArm", "LeftForeArm", "LeftHand"]:
    print(f"  {b} -> parent: {hierarchy.get(b)}")
