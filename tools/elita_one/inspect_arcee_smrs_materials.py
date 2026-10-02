import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        mesh_id = tree.get("m_Mesh", {}).get("m_PathID")
        mats = tree.get("m_Materials", [])
        mat_ids = [m.get("m_PathID") for m in mats]
        
        # find GO name
        go_name = "unknown"
        for o in env.objects:
            if o.path_id == go_id:
                go_name = o.read_typetree().get("m_Name", "")
                break
        print(f"SMR on '{go_name}' (PID: {go_id}) -> Materials: {mat_ids}")
