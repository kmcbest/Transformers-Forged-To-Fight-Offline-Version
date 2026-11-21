import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Swoop\Ramjet")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Extracting Ramjet textures from {BUNDLE_PATH} -> {OUT_DIR}")
env = UnityPy.load(str(BUNDLE_PATH))

extracted = 0
for obj in env.objects:
    if obj.type.name == "Texture2D":
        d = obj.read()
        name = d.m_Name
        if any(k in name.lower() for k in ["main", "wpn", "misc", "tform"]):
            try:
                img = d.image
                if img:
                    out_path = OUT_DIR / f"{name}.png"
                    img.save(str(out_path))
                    print(f"  Saved {name}.png ({img.size[0]}x{img.size[1]})")
                    extracted += 1
            except Exception as e:
                print(f"  Error extracting {name}: {e}")

print(f"[✓] Extracted {extracted} Ramjet textures to {OUT_DIR}")
