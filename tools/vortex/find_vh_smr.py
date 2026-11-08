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
    vh_bones = set(json.load(f))

# Find the SkinnedMeshRenderer for cha_grindor_cin_rotf_01
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        data = obj.read_typetree()
        mesh_ref = data.get("m_Mesh")
        bones = data.get("m_Bones", [])
        if len(bones) == 45:
            print("Found 45-bone vehicle SMR!")
            # Get the root bone
            root_ref = data.get("m_RootBone")
            if root_ref:
                root_obj = obj.assets_file.objects[root_ref["m_PathID"]]
                root_t = root_obj.read_typetree()
                root_go = obj.assets_file.objects[root_t["m_GameObject"]["m_PathID"]].read_typetree()
                print("Root bone:", root_go["m_Name"])
            # Print bone transforms and parents
            parents = {}
            for b_ref in bones:
                b_t_obj = obj.assets_file.objects[b_ref["m_PathID"]]
                b_t = b_t_obj.read_typetree()
                b_go = obj.assets_file.objects[b_t["m_GameObject"]["m_PathID"]].read_typetree()
                b_name = b_go["m_Name"]
                parent_ref = b_t.get("m_Father")
                p_name = None
                if parent_ref and parent_ref["m_PathID"] != 0:
                    p_t_obj = obj.assets_file.objects[parent_ref["m_PathID"]]
                    p_t = p_t_obj.read_typetree()
                    p_go = obj.assets_file.objects[p_t["m_GameObject"]["m_PathID"]].read_typetree()
                    p_name = p_go["m_Name"]
                parents[b_name] = p_name
            print(f"Mapped parents for {len(parents)} bones: {parents}")
            with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_45_vh_hierarchy.json", "w", encoding="utf-8") as f:
                json.dump({"bone_order": list(vh_bones), "parents": parents}, f, indent=2)
            break
