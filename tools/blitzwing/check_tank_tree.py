import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy
import binascii

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

# Let's inspect the hierarchy starting from 'transformed'
tank_t = None
for o in env.objects:
    if o.type.name == "GameObject":
        t = o.read_typetree()
        if t.get("m_Name") == "transformed":
            for c in t.get("m_Component", []):
                cid = c.get("component", {}).get("m_PathID")
                if cid in obj_map and obj_map[cid].type.name == "Transform":
                    tank_t = obj_map[cid].read_typetree()
                    break

def print_tree(t_dict, indent=""):
    go_id = t_dict.get("m_GameObject", {}).get("m_PathID")
    go_name = obj_map[go_id].read_typetree().get("m_Name") if go_id in obj_map else "Unknown"
    print(f"{indent}- GO: '{go_name}'")
    for child in t_dict.get("m_Children", []):
        cid = child.get("m_PathID")
        if cid in obj_map:
            print_tree(obj_map[cid].read_typetree(), indent + "  ")

if tank_t:
    print_tree(tank_t)
