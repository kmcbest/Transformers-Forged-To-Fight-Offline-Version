# UTF-8 encoding
import dnfile
import shutil
from pathlib import Path

def patch_heroportrait():
    dll_path = Path(r"D:\Agent\tftf-darabat\build\Assembly-CSharp.dll")
    backup_path = Path(r"D:\Agent\tftf-darabat\build\Assembly-CSharp.dll.bak")
    
    if not backup_path.exists():
        shutil.copy2(dll_path, backup_path)
        print(f"Backed up to {backup_path}")
        
    pe = dnfile.dnPE(str(dll_path))
    
    # Target in HeroPortrait::SetEnabledItems:
    # IL_0255: ldarg.0 (02)
    # IL_0256: ldarg.0 (02)
    # IL_0257: call UpdateContainerAnchors (28 b2 04 00 06)
    # IL_025c: call StartCoroutine (28 cc 00 00 0a)
    #
    # Patch to:
    # IL_0255: ldarg.0 (02)
    # IL_0256: ldarg.0 (02)
    # IL_0257: call UpdateContainerAnchors (28 b2 04 00 06)
    # IL_025c: call Coroutines::Run (28 a3 00 00 0a)
    
    rva = 0x11cc8
    method_offset = pe.get_offset_from_rva(rva)
    pe.close()
    del pe
    
    with open(dll_path, "rb") as f:
        data = bytearray(f.read())
        
    # Locate IL_0255:
    target_pattern = bytes.fromhex("02 02 28 b2 04 00 06 28 cc 00 00 0a")
    idx = data.find(target_pattern, method_offset)
    if idx == -1 or idx > method_offset + 0x300:
        raise Exception(f"Target pattern not found near 0x{method_offset:X}!")
        
    replacement_pattern = bytes.fromhex("02 02 28 b2 04 00 06 28 a3 00 00 0a")
    data[idx : idx + len(replacement_pattern)] = replacement_pattern
    print(f"Patched HeroPortrait::SetEnabledItems StartCoroutine -> Coroutines.Run at file offset 0x{idx:X}")
    
    with open(dll_path, "wb") as f:
        f.write(data)
    print("Successfully saved patched Assembly-CSharp.dll")

if __name__ == "__main__":
    patch_heroportrait()
