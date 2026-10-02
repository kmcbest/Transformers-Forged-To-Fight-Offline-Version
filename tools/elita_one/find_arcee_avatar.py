import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

avatars = []
for obj in env.objects:
    if obj.type.name == "Avatar":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        avatars.append((name, obj.path_id))

print(f"Total Avatars in Arcee bundle: {len(avatars)}")
for name, pid in avatars:
    print(f"  Avatar: '{name}', path_id={pid}")
