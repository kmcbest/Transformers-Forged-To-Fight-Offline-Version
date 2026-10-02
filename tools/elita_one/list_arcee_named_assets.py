import UnityPy
from pathlib import Path

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name in ["Texture2D", "Material", "Mesh"]:
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        print(f"[{obj.type.name}] {name}")
