import UnityPy
from pathlib import Path

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name in ["Texture2D", "Material", "GameObject", "Mesh"]:
        data = obj.read()
        print(f"[{obj.type.name}] {getattr(data, 'name', '')}")
