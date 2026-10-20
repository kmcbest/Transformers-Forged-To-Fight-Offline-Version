# UTF-8 encoding
import dnfile
import shutil
from pathlib import Path

def patch():
    dll_path = Path(r"D:\Agent\tftf-darabat\build\Assembly-CSharp-firstpass.dll")
    backup_path = Path(r"D:\Agent\tftf-darabat\build\Assembly-CSharp-firstpass.dll.orig")
    
    if not backup_path.exists():
        shutil.copy2(dll_path, backup_path)
        print(f"Original backed up to {backup_path}")
        
    pe = dnfile.dnPE(str(dll_path))
    with open(dll_path, "rb") as f:
        data = bytearray(f.read())
        
    # 1. Patch <UITextureRef.LoadTexture>b__66_0
    # Target RVA: 0x7B5F4
    off1 = pe.get_offset_from_rva(0x7B5F4)
    # Target site: after set_textureLoaded (0x14 from method start, after 12 byte header)
    patch_site1 = off1 + 12 + 0x14
    
    # Verify existing bytes at patch_site1:
    orig1 = bytes(data[patch_site1 : patch_site1 + 38])
    expected1_start = bytes.fromhex("02 28 c2 15 00 06 2c 20")
    assert orig1.startswith(expected1_start), f"Unexpected orig1: {orig1[:8].hex()}"
    
    # Replacement:
    # ldarg.0; ldc.r4 1.0; callvirt set_alpha (0x06000258)  [11 bytes]
    # ldarg.0; ldc.i4.1; callvirt set_isRendering (0x06000122) [7 bytes]
    # 20x nop [20 bytes]
    # Total: 38 bytes
    repl1 = bytes.fromhex("02 22 00 00 80 3f 6f 58 02 00 06") + \
            bytes.fromhex("02 17 6f 22 01 00 06") + \
            bytes([0x00] * 20)
    assert len(repl1) == 38
    data[patch_site1 : patch_site1 + 38] = repl1
    print(f"Patched <UITextureRef.LoadTexture>b__66_0 at 0x{patch_site1:X}")
    
    # 2. Patch <UIScalingTextureRef.LoadTexture>b__50_0
    # Target RVA: 0x7F88C
    off2 = pe.get_offset_from_rva(0x7F88C)
    patch_site2 = off2 + 12 + 0x14
    
    orig2 = bytes(data[patch_site2 : patch_site2 + 27])
    expected2_start = bytes.fromhex("02 28 a9 16 00 06 2c 15")
    assert orig2.startswith(expected2_start), f"Unexpected orig2: {orig2[:8].hex()}"
    
    # Replacement: 11 bytes + 7 bytes + 9 nops = 27 bytes
    repl2 = bytes.fromhex("02 22 00 00 80 3f 6f 58 02 00 06") + \
            bytes.fromhex("02 17 6f 22 01 00 06") + \
            bytes([0x00] * 9)
    assert len(repl2) == 27
    data[patch_site2 : patch_site2 + 27] = repl2
    print(f"Patched <UIScalingTextureRef.LoadTexture>b__50_0 at 0x{patch_site2:X}")
    
    pe.close()
    del pe
    with open(dll_path, "wb") as f:
        f.write(data)
    print("Successfully saved patched Assembly-CSharp-firstpass.dll!")

if __name__ == "__main__":
    patch()
