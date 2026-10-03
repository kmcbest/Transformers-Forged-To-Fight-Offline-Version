import capstone

so_path = "build/libil2cpp-arm64-patched.so"
with open(so_path, "rb") as f:
    code = f.read()

md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

start = 0x9572d0
end = start + 0x60
print(f"=== Disassembly 0x{start:x} to 0x{end:x} ===")
chunk = code[start:end]
for insn in md.disasm(chunk, start):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")
