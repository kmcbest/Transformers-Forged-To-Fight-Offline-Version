import struct

# Look for elf symbols in libil2cpp.so
so_path = "extracted_apk/lib/arm64-v8a/libil2cpp.so"
with open(so_path, "rb") as f:
    data = f.read()

# Let's check if there are symbols or strings near 0x95bdec / 0x95c428
print(f"Loaded libil2cpp.so: {len(data)} bytes")
# Check bytes at 0x95bdec:
off = 0x95bdec
print(f"Bytes at {hex(off)}: {data[off:off+16].hex()}")
off_c = 0x95c428
print(f"Bytes at {hex(off_c)}: {data[off_c:off_c+16].hex()}")
