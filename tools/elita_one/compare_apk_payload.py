import zipfile
from pathlib import Path

bin1 = Path("build/payload_test.bin").read_bytes()
with zipfile.ZipFile("build/Transformers-9.2-offline-blender.apk", "r") as z:
    bin2 = z.read("assets/tftf_offline_payload.bin")

print(f"payload_test.bin len: {len(bin1)}")
print(f"tftf_offline_payload.bin len: {len(bin2)}")
print(f"Identical? {bin1 == bin2}")
