import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile
import json
from pathlib import Path

apk_path = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
with zipfile.ZipFile(apk_path, "r") as z:
    toc_data = json.loads(z.read("assets/brawl_gs_odr/toc.txt").decode("utf-8"))
    bundle_size = z.getinfo("assets/assetpack/brawl_gs_odr/brawl_gs.assetbundle").file_size
    toc_size = toc_data["bundles"]["brawl_gs"]["size"]
    print(f"Bundle size: {bundle_size}, TOC size: {toc_size}, Matches: {bundle_size == toc_size}")
