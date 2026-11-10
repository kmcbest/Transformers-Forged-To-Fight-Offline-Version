import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
out_prowl_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\Prowl")
out_prowl_dir.mkdir(parents=True, exist_ok=True)

env = UnityPy.load(str(p_prowl))

for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        if name:
            img = data.image
            out_p = out_prowl_dir / f"{name}.png"
            img.save(out_p)
            print(f"  Extracted Texture2D: {name} ({img.size}) -> {out_p.name}")

print(f"\n[✓] All Prowl textures extracted to {out_prowl_dir}")
