import sys
import zipfile
from pathlib import Path

apk_path = Path("build/Transformers-9.2-offline-blender.apk")
if not apk_path.exists():
    print(f"Error: {apk_path} does not exist!")
    sys.exit(1)

with zipfile.ZipFile(apk_path, "r") as z:
    names = z.namelist()
    print(f"Total files in APK: {len(names)}")
    elita_files = [n for n in names if "elita" in n.lower()]
    print(f"Elita files in APK ({len(elita_files)}):")
    for f in elita_files:
        print("  -", f)

    # Check payload.bin inside APK
    payload_name = "assets/tftf_offline_payload.bin"
    if payload_name in names:
        payload_data = z.read(payload_name)
        print(f"{payload_name} size: {len(payload_data)} bytes")
        # Check if elita_one_gs is in payload_data
        print(f"b'elita_one_gs' in payload? {b'elita_one_gs' in payload_data}")
        zh_name_bytes = "艾丽塔".encode("utf-8")
        print(f"艾丽塔 in payload? {zh_name_bytes in payload_data}")
    else:
        print(f"{payload_name} NOT FOUND in APK!")
