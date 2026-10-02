import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

print(f"=== Inspecting {bundle_path.name} ===")
for obj in env.objects:
    if obj.type.name in ["Mesh", "Material", "Texture2D", "GameObject"]:
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        if obj.type.name != "GameObject" or "arcee" in name.lower() or "prefab" in name.lower():
            print(f"[{obj.type.name:20s}] PID: {obj.path_id:20d} | Name: {name}")

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mesh_ptr = tree.get("m_Mesh", {}).get("m_PathID")
        go_ptr = tree.get("m_GameObject", {}).get("m_PathID")
        print(f"[SkinnedMeshRenderer] PID: {obj.path_id:20d} | Mesh PID: {mesh_ptr} | GO PID: {go_ptr}")
