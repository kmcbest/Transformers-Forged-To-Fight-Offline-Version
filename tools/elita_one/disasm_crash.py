import capstone

so_path = "build/libil2cpp-arm64-patched.so"
with open(so_path, "rb") as f:
    code = f.read()

md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)

# Disassemble around 0x95bdec
start = 0x95bd00
end = 0x95be20
print(f"=== Disassembly 0x{start:x} to 0x{end:x} ===")
chunk = code[start:end]
for insn in md.disasm(chunk, start):
    marker = "===> " if insn.address == 0x95bdec else "     "
    print(f"{marker}0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

# Also disassemble 0x95c428 (caller)
start_c = 0x95c400
end_c = 0x95c450
print(f"\n=== Disassembly 0x{start_c:x} to 0x{end_c:x} ===")
chunk_c = code[start_c:end_c]
for insn in md.disasm(chunk_c, start_c):
    marker = "===> " if insn.address == 0x95c428 else "     "
    print(f"{marker}0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")
