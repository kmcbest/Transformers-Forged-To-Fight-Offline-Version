import UnityPy
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

bone_names_78 = []
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        s = obj.read()
        mesh_obj = s.m_Mesh.read() if getattr(s, "m_Mesh", None) else None
        mname = getattr(mesh_obj, "m_Name", getattr(mesh_obj, "name", "")) if mesh_obj else ""
        if mname == "cha_grindor_cin_rotf_00":
            for b in getattr(s, "m_Bones", []):
                t_obj = b.read()
                go_ptr = getattr(t_obj, "m_GameObject", None)
                if go_ptr:
                    go_obj = go_ptr.read()
                    bname = getattr(go_obj, "m_Name", getattr(go_obj, "name", "None"))
                else:
                    bname = "Unknown"
                bone_names_78.append(bname)
            break

print(f"Total bones in Grindor 00 SMR: {len(bone_names_78)}")
for idx, bn in enumerate(bone_names_78):
    print(f"  [{idx:2d}] {bn}")

with open(r"E:\Agent\TFTF-blender\tools\vortex\grindor_78_bones.json", "w", encoding="utf-8") as f:
    json.dump(bone_names_78, f, indent=2)
