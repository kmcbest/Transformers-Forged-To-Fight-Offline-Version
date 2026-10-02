import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle")
env = UnityPy.load(str(bundle_path))

print(f"=== Inspecting {bundle_path.name} ===")
for obj in env.objects:
    if obj.type.name in ["GameObject", "Mesh", "SkinnedMeshRenderer", "Material", "Texture2D"]:
        data = obj.read()
        name = getattr(data, "name", "unknown")
        print(f"[{obj.type.name}] PID: {obj.path_id:20d} | Name: {name}")
