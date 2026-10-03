# Check strings referenced by code near 0x95b000 - 0x95c000
so_path = "build/libil2cpp-arm64-patched.so"
with open(so_path, "rb") as f:
    data = f.read()

# Let's search for adrp/add or literal pool or string references in that function
# Let's search for 0x95b95c callers or references in data
import struct
target = struct.pack('<Q', 0x95b95c)
for i in range(0, len(data) - 8, 8):
    if data[i:i+8] == target:
        print(f"Pointer to 0x95b95c at {hex(i)}")

# Let's search if any string is within [0x950000, 0x960000]
# Or let's search global metadata
