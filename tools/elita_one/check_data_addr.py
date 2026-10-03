# Check strings or global symbols near 0x243eeb8
so_path = "build/libil2cpp-arm64-patched.so"
with open(so_path, "rb") as f:
    data = f.read()

addr = 0x243eeb8
print(f"Bytes at {hex(addr)}: {data[addr:addr+32].hex()}")
# Check if there is string nearby:
for o in range(max(0, addr - 200), min(len(data), addr + 200)):
    if data[o:o+4] in [b'Init', b'Anim', b'Clip', b'Play', b'Sksh', b'Char']:
        end = data.find(b'\x00', o)
        print(f"String at {hex(o)}: {data[o:end].decode('ascii', errors='ignore')}")
