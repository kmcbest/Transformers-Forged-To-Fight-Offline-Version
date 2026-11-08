import UnityPy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

# Let's find the main Grindor_Cin_ROTF GameObject and traverse its transform hierarchy
def print_hierarchy(t_obj, depth=0):
    t = t_obj.read_typetree()
    go = t_obj.assets_file.objects[t["m_GameObject"]["m_PathID"]].read_typetree()
    name = go["m_Name"]
    pos = t["m_LocalPosition"]
    print(f"{'  '*depth}{name} (pos: {pos['x']:.2f}, {pos['y']:.2f}, {pos['z']:.2f})")
    for child in t.get("m_Children", []):
        child_obj = t_obj.assets_file.objects[child["m_PathID"]]
        print_hierarchy(child_obj, depth + 1)

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read_typetree()
        if data.get("m_Name") == "Grindor_Cin_ROTF":
            print(f"Root: {data['m_Name']}")
            # Find its Transform
            for comp in data.get("m_Component", []):
                comp_obj = obj.assets_file.objects[comp["component"]["m_PathID"]]
                if comp_obj.type.name == "Transform":
                    print_hierarchy(comp_obj)
                    break
            break
