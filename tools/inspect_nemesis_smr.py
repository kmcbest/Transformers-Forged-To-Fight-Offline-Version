import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        data = obj.read()
        tree = obj.read_typetree()
        # Find which GameObject owns this SMR
        go_ref = tree.get("m_GameObject", {})
        mats = tree.get("m_Materials", [])
        mesh_ref = tree.get("m_Mesh", {})
        print(f"SMR on GO PathID {go_ref.get('m_PathID')}, Mesh PathID {mesh_ref.get('m_PathID')}, Mats count: {len(mats)}")
        for m in mats:
            print(f"   Mat PathID: {m.get('m_PathID')}")
