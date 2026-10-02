import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        v_count = tree.get("m_VertexData", {}).get("m_VertexCount", 0)
        aabb = tree.get("m_LocalAABB", {})
        print(f"Mesh: {name:35s} | Verts: {v_count:6d} | AABB Center: {aabb.get('m_Center')} Extent: {aabb.get('m_Extent')}")

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        mesh_id = tree.get("m_Mesh", {}).get("m_PathID")
        # find GO name
        go_name = "unknown"
        for o in env.objects:
            if o.path_id == go_id:
                go_name = o.read_typetree().get("m_Name", "")
                break
        print(f"SMR on GO '{go_name}' (PID: {go_id}) -> Mesh PID: {mesh_id}")
