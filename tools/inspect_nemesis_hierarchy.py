import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
env = UnityPy.load(str(bundle_path))

# Map path_id to object/name
id_map = {}
for obj in env.objects:
    try:
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        id_map[obj.path_id] = (obj.type.name, name)
    except:
        pass

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        mesh_id = tree.get("m_Mesh", {}).get("m_PathID")
        mats = tree.get("m_Materials", [])
        
        go_info = id_map.get(go_id, ("GO", "Unknown"))
        mesh_info = id_map.get(mesh_id, ("Mesh", "Unknown"))
        
        mat_names = [id_map.get(m.get("m_PathID"), ("Mat", "Unknown"))[1] for m in mats]
        print(f"GO: {go_info[1]} | Mesh: {mesh_info[1]} | Mats: {mat_names}")
