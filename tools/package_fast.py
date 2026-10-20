import os
import sys
import subprocess
import shutil
import zipfile
from pathlib import Path

def main():
    print("=== Packaging revival launcher APK (Reusing existing shaders.bundle & patched DLLs) ===")
    
    # 1. Base Paths
    build_dir = Path(r"D:\Agent\tftf-darabat\build")
    src_apk = build_dir / "pulled_base.apk"
    csharp_dll = build_dir / "Assembly-CSharp.dll"
    firstpass_dll = build_dir / "Assembly-CSharp-firstpass.dll"
    shader_bundle = build_dir / "shaders.bundle"
    
    # Toolchain paths
    zipalign_exe = Path(r"D:\Agent\tftf\toolchain\android-13\zipalign.exe")
    apksigner_bat = Path(r"D:\Agent\tftf\toolchain\android-13\apksigner.bat")
    keystore = Path(r"D:\Agent\tftf\build\debug.keystore")
    java_home = Path(r"D:\Agent\tftf\toolchain\jdk-17")
    
    # Temp and final output
    temp_unsigned = build_dir / "temp_unsigned.apk"
    temp_aligned = build_dir / "temp_aligned.apk"
    final_apk = build_dir / "tftf-revival-launcher-latest.apk"
    
    # Check prerequisites
    for p in [src_apk, csharp_dll, firstpass_dll, shader_bundle, zipalign_exe, apksigner_bat, keystore]:
        if not p.exists():
            print(f"ERROR: Missing required file: {p}")
            sys.exit(1)
            
    print(f"Source base APK: {src_apk} ({src_apk.stat().st_size} bytes)")
    print(f"Assembly-CSharp.dll: {csharp_dll} ({csharp_dll.stat().st_size} bytes)")
    print(f"Assembly-CSharp-firstpass.dll: {firstpass_dll} ({firstpass_dll.stat().st_size} bytes)")
    print(f"shaders.bundle: {shader_bundle} ({shader_bundle.stat().st_size} bytes)")
    
    with open(csharp_dll, "rb") as f:
        csharp_data = f.read()
    with open(firstpass_dll, "rb") as f:
        firstpass_data = f.read()
    with open(shader_bundle, "rb") as f:
        shader_data = f.read()
        
    if temp_unsigned.exists():
        temp_unsigned.unlink()
    if temp_aligned.exists():
        temp_aligned.unlink()
    if final_apk.exists():
        final_apk.unlink()

    print("\n--- Injecting patched files into unsigned APK ---")
    written_shader_bundle = False
    with zipfile.ZipFile(src_apk, "r") as zin, zipfile.ZipFile(temp_unsigned, "w") as zout:
        for item in zin.infolist():
            # Strip old signature
            if item.filename.startswith("META-INF/") and (
                item.filename.endswith(".SF") or item.filename.endswith(".RSA") or item.filename.endswith(".MF")
            ):
                continue
            if item.filename == "assets/bin/Data/Managed/Assembly-CSharp.dll":
                print("  Injecting Assembly-CSharp.dll...")
                zout.writestr(item.filename, csharp_data, compress_type=zipfile.ZIP_DEFLATED)
            elif item.filename == "assets/bin/Data/Managed/Assembly-CSharp-firstpass.dll":
                print("  Injecting Assembly-CSharp-firstpass.dll...")
                zout.writestr(item.filename, firstpass_data, compress_type=zipfile.ZIP_DEFLATED)
            elif item.filename == "assets/shaders.bundle":
                print("  Injecting assets/shaders.bundle (ZIP_STORED)...")
                zout.writestr(item.filename, shader_data, compress_type=zipfile.ZIP_STORED)
                written_shader_bundle = True
            else:
                data = zin.read(item.filename)
                zout.writestr(item, data)

        if not written_shader_bundle:
            print("  Adding new entry assets/shaders.bundle (ZIP_STORED)...")
            zinfo = zipfile.ZipInfo("assets/shaders.bundle")
            zinfo.compress_type = zipfile.ZIP_STORED
            zout.writestr(zinfo, shader_data)

    print(f"Unsigned APK created: {temp_unsigned.stat().st_size} bytes")

    print("\n--- Running zipalign ---")
    subprocess.run([str(zipalign_exe), "-f", "-p", "4", str(temp_unsigned), str(temp_aligned)], check=True)
    print(f"Aligned APK created: {temp_aligned.stat().st_size} bytes")

    print("\n--- Signing APK with apksigner ---")
    env = os.environ.copy()
    env["JAVA_HOME"] = str(java_home)
    env["PATH"] = f"{java_home / 'bin'};{env.get('PATH', '')}"

    cmd_sign = [
        str(apksigner_bat), "sign",
        "--ks", str(keystore),
        "--ks-pass", "pass:android",
        "--out", str(final_apk),
        str(temp_aligned)
    ]
    subprocess.run(cmd_sign, check=True, env=env)
    print(f"Signed APK created: {final_apk} ({final_apk.stat().st_size} bytes)")

    # Clean up temp files
    if temp_unsigned.exists():
        temp_unsigned.unlink()
    if temp_aligned.exists():
        temp_aligned.unlink()

    print("\n=======================================================")
    print("=== PACKAGING SUCCESSFUL! ===")
    print(f"Output APK: {final_apk}")
    print("=======================================================")

if __name__ == "__main__":
    main()
