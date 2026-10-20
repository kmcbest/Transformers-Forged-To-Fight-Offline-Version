# UTF-8 encoding
import dnfile
import shutil
from pathlib import Path

def patch_firstpass_fade():
    dll_path = Path(r"D:\Agent\tftf-darabat\build\Assembly-CSharp-firstpass.dll")
    backup_path = Path(r"D:\Agent\tftf-darabat\build\Assembly-CSharp-firstpass.dll.bak")
    
    if not backup_path.exists():
        shutil.copy2(dll_path, backup_path)
        print(f"Backed up to {backup_path}")
        
    pe = dnfile.dnPE(str(dll_path))
    with open(dll_path, "rb") as f:
        data = bytearray(f.read())
        
    # 1. UITextureRef::StartFadeTextureIn
    # Original:
    # 62 (tiny header, code_size=24)
    # 02                ldarg.0
    # 22 00 00 00 00    ldc.r4 0.0
    # 6f 58 02 00 06    callvirt set_alpha (0x06000258)
    # 02 28 e4 15 00 06 call UpdateAlpha
    # 28 d6 02 00 06    call Coroutines::Run
    # 26                pop
    # 2a                ret
    #
    # Patch to:
    # 02                ldarg.0
    # 22 00 00 80 3f    ldc.r4 1.0
    # 6f 58 02 00 06    callvirt set_alpha (0x06000258)
    # 2a                ret
    # 00 * 12           nop padding
    
    rva1 = 0x7B515
    off1 = pe.get_offset_from_rva(rva1)
    code_off1 = off1 + 1 # tiny header is 1 byte
    
    orig_code1 = bytes(data[code_off1 : code_off1 + 24])
    expected1 = bytes.fromhex("02 22 00 00 00 00 6f 58 02 00 06 02 28 e4 15 00 06 28 d6 02 00 06 26 2a")
    assert orig_code1 == expected1, f"Expected {expected1.hex()}, got {orig_code1.hex()}"
    
    # New code: ldarg.0; ldc.r4 1.0 (3F800000 in little endian = 00 00 80 3f); callvirt set_alpha; ret; 12x nop
    new_code1 = bytes.fromhex("02 22 00 00 80 3f 6f 58 02 00 06 2a") + bytes([0x00] * 12)
    assert len(new_code1) == 24
    data[code_off1 : code_off1 + 24] = new_code1
    print(f"Patched UITextureRef::StartFadeTextureIn at 0x{code_off1:X}")
    
    # 2. UIScalingTextureRef::StartFadeTextureIn
    # Original:
    # 66 (tiny header, code_size=25)
    # 02 22 00 00 00 00 6f 58 02 00 06 02 02 28 c4 16 00 06 28 d7 02 00 06 26 2a
    rva2 = 0x7F806
    off2 = pe.get_offset_from_rva(rva2)
    code_off2 = off2 + 1
    
    orig_code2 = bytes(data[code_off2 : code_off2 + 25])
    expected2 = bytes.fromhex("02 22 00 00 00 00 6f 58 02 00 06 02 02 28 c4 16 00 06 28 d7 02 00 06 26 2a")
    assert orig_code2 == expected2, f"Expected {expected2.hex()}, got {orig_code2.hex()}"
    
    new_code2 = bytes.fromhex("02 22 00 00 80 3f 6f 58 02 00 06 2a") + bytes([0x00] * 13)
    assert len(new_code2) == 25
    data[code_off2 : code_off2 + 25] = new_code2
    print(f"Patched UIScalingTextureRef::StartFadeTextureIn at 0x{code_off2:X}")
    
    pe.close()
    del pe
    with open(dll_path, "wb") as f:
        f.write(data)
    print("Successfully wrote patched Assembly-CSharp-firstpass.dll")

if __name__ == "__main__":
    patch_firstpass_fade()
