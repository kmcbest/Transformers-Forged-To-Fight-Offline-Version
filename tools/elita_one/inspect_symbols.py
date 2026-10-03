import struct

so_path = "build/libil2cpp-arm64-patched.so"
with open(so_path, "rb") as f:
    # Read ELF header
    e_ident = f.read(16)
    if e_ident[:4] != b'\x7fELF':
        print("Not an ELF file")
        exit(1)
    
    # 64-bit ELF
    f.seek(32)
    e_shoff = struct.unpack('<Q', f.read(8))[0]
    f.seek(48)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack('<HHH', f.read(6))

    # Read section headers
    f.seek(e_shoff)
    sections = []
    for i in range(e_shnum):
        sec = f.read(e_shentsize)
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, sh_link, sh_info, sh_addralign, sh_entsize = struct.unpack('<IIQQQQIIQQ', sec)
        sections.append({
            'name_idx': sh_name, 'type': sh_type, 'flags': sh_flags,
            'addr': sh_addr, 'offset': sh_offset, 'size': sh_size,
            'link': sh_link, 'info': sh_info, 'entsize': sh_entsize
        })
    
    # Section header string table
    shstr = sections[e_shstrndx]
    f.seek(shstr['offset'])
    shstrtab = f.read(shstr['size'])
    
    def get_sec_name(idx):
        end = shstrtab.find(b'\x00', idx)
        return shstrtab[idx:end].decode('ascii', errors='ignore')

    symtabs = [s for s in sections if s['type'] in (2, 11)] # SHT_SYMTAB, SHT_DYNSYM
    print(f"Found {len(symtabs)} symbol tables")
    
    for s in symtabs:
        strtab_sec = sections[s['link']]
        f.seek(strtab_sec['offset'])
        strtab = f.read(strtab_sec['size'])
        
        num_syms = s['size'] // s['entsize']
        f.seek(s['offset'])
        for _ in range(num_syms):
            sym = f.read(s['entsize'])
            st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack('<IBBHQQ', sym)
            if st_value in [0x95bdec, 0x95bd30, 0x95b998, 0x95c428] or (0x95b000 <= st_value <= 0x95d000):
                end = strtab.find(b'\x00', st_name)
                name = strtab[st_name:end].decode('utf-8', errors='ignore')
                print(f"Sym at {hex(st_value)}: {name} (size {st_size})")

