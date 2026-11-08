import UnityPy
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_bones.json", "r", encoding="utf-8") as f:
    vh_bone_order = json.load(f)

parents = {}

def traverse(t_obj, parent_name=None):
    t = t_obj.read_typetree()
    go = t_obj.assets_file.objects[t["m_GameObject"]["m_PathID"]].read_typetree()
    name = go["m_Name"]
    if name in vh_bone_order:
        parents[name] = parent_name
        current_parent = name
    else:
        current_parent = parent_name
        
    for child in t.get("m_Children", []):
        child_obj = t_obj.assets_file.objects[child["m_PathID"]]
        traverse(child_obj, current_parent)

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read_typetree()
        if "vh" in data.get("m_Name", "").lower() or "vehicle" in data.get("m_Name", "").lower() or data.get("m_Name") == "Grindor_Cin_ROTF_01":
            print("Found candidate vehicle GO:", data.get("m_Name"))
            for comp in data.get("m_Component", []):
                comp_obj = obj.assets_file.objects[comp["component"]["m_PathID"]]
                if comp_obj.type.name == "Transform":
                    traverse(comp_obj)
                    break
            if len(parents) >= 40:
                break

print(f"Total vehicle bones with parents: {len(parents)} / {len(vh_bone_order)}")
missing = [b for b in vh_bone_order if b not in parents]
print(f"Missing vehicle bones: {missing}")

hierarchy_data = {
    "bone_order": vh_bone_order,
    "parents": parents
}

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_hierarchy.json", "w", encoding="utf-8") as f:
    json.dump(hierarchy_data, f, indent=2)

print("Saved grindor_45_vh_hierarchy.json successfully!")
