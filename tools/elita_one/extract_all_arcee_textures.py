import sys
import UnityPy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = Path("extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle")
out_dir = Path("toolchain/unity_build_project/Assets/ElitaOne/Arcee")
out_dir.mkdir(parents=True, exist_ok=True)

env = UnityPy.load(str(bundle_path))
count = 0
for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        name = getattr(data, 'name', getattr(data, 'm_Name', ''))
        if name:
            img = data.image
            out_file = out_dir / f"{name}.png"
            img.save(str(out_file))
            print(f"[+] Extracted texture: {name} -> {out_file.name}")
            count += 1

print(f"Total textures extracted: {count}")
