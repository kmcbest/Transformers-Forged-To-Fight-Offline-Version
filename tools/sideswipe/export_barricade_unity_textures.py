import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

BUNDLE_PATH = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle"
OUT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Sideswipe\Barricade")
OUT_DIR.mkdir(parents=True, exist_ok=True)

env = UnityPy.load(BUNDLE_PATH)
for obj in env.objects:
    if obj.type.name == "Texture2D":
        data = obj.read()
        name = getattr(data, "m_Name", getattr(data, "name", str(obj.path_id)))
        try:
            img = data.image
            out_fp = OUT_DIR / f"tex_{name}.png"
            img.save(str(out_fp))
            print(f"Saved {out_fp.name} ({img.size})")
        except Exception as e:
            print(f"Error saving {name}: {e}")
