import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

def crc32_hash(s):
    import zlib
    return zlib.crc32(s.encode('utf-8'))

with open(r"E:\Agent\TFTF-blender\tools\blitzwing\megatron_tank_21_authoritative_bindposes.json", "r") as f:
    d = json.load(f)

print("Megatron Tank bone hashes:")
for name in d.get("bone_names", []):
    print(f"  {name}: {crc32_hash(name)}")
