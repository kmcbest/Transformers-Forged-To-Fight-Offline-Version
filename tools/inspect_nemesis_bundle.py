import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
if not bundle_path.exists():
    bundle_path = Path(r"E:\Agent\TFTF-blender\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")

print(f"Loading {bundle_path}...")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    tname = obj.type.name
    try:
        data = obj.read()
        name = getattr(data, "name", getattr(data, "m_Name", ""))
        print(f"[{tname}] {name} (PathID: {obj.path_id})")
    except Exception as e:
        print(f"[{tname}] (Error reading: {e})")
