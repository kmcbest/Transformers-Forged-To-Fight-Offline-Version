import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile, json
from pathlib import Path

APK = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
with zipfile.ZipFile(APK, "r") as z:
    for name in z.namelist():
        if "brawl_gs" in name or "tarn_gs" in name or "megatron_cin_rotf" in name:
            if name.endswith("toc.txt"):
                print(f"\n=== {name} ===")
                try:
                    data = json.loads(z.read(name).decode("utf-8"))
                    print(json.dumps(data, indent=2))
                except Exception as e:
                    print(f"Error: {e}")
