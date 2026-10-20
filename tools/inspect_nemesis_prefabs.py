import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
env = UnityPy.load(str(bundle_path))

print("=== ROOT GAMEOBJECTS / PREFABS ===")
for obj in env.objects:
    if obj.type.name in ["GameObject", "Prefab"]:
        try:
            tree = obj.read_typetree()
            name = tree.get("m_Name", "")
            # check if it looks like a character prefab
            if "nemesis" in name.lower() or "optimus" in name.lower() or "bot" in name.lower() or "actor" in name.lower():
                print(f"[{obj.type.name}] {name} (PathID: {obj.path_id})")
        except Exception as e:
            pass
