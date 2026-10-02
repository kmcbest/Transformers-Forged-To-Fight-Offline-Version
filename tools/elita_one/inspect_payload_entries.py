import struct
import json
from pathlib import Path

payload_file = Path("build/payload_test.bin")
data = payload_file.read_bytes()

# Parse the payload format
# In export_payload.py:
# File format: magic, count, then index of (key, offset, size), then data block
# Let's see how export_payload packs it:
print(f"Payload size: {len(data)}")

# Let's search for keys
keys_to_check = [b"@roster", b"@userdata:template", b"@logindata:zh", b"elita_one_gs"]
for k in keys_to_check:
    pos = data.find(k)
    print(f"Key {k}: found at {pos}")

# Check if elita_one_gs is in the decrypted/unpacked entries
