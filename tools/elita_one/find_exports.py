# Find exported il2cpp symbols near 0x95c000
so_path = "build/libil2cpp-arm64-patched.so"
with open(so_path, "rb") as f:
    data = f.read()

# Let's search for "il2cpp_" strings in data:
# Or find the symbol table
import re
matches = re.finditer(b'il2cpp_[a-zA-Z0-9_]+', data)
for m in list(matches)[:20]:
    print(m.group().decode())
