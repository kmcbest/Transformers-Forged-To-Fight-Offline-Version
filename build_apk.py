#!/usr/bin/env python3
"""Build and sign offline APK for Transformers Forged to Fight.
Dynamically sets output APK name based on current git branch.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
BUILD_DIR.mkdir(exist_ok=True)

def get_git_branch() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
           #heck=True
        )
        branch = res.stdout.strip().replace("/", "-")
        return branch if branch else "custom"
    except Exception:
        return "custom"


def main():
    branch = get_git_branch()
    output_apk_name = f'Transformers-9.2-offline-branch.apk'.replace('branch', branch)
    output_apk_path = BUILD_DIR / output_apk_name
    print(f"=== Building Offline APK for branch [{branch}] ===")
    print(f"Target APK: {output_apk_path}")

    # 1. Compile native hook
    clang = ROOT / "toolchain" / "android-ndk-r26d" / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"
    hook_so = ROOT / "tools" / "nativehook" / "libdothook.so"
    hook_c = ROOT / "tools" / "nativehook" / "hook.c"
    inapk_server_c = ROOT / "tools" / "nativehook" / "inapk_server.c"

    print("\n[1/5] Compiling libdothook.so...")
    subprocess.run([
        str(clang), "-shared", "-O2", "-fPIC", "-Wl,-soname,libdothook.so",
        "-o", str(hook_so), str(hook_c), str(inapk_server_c), "-llog"
    ], check=True, cwd=ROOT)

    # 2. Export offline payload
    print("\n[2/5] Exporting offline payload...")
    payload_bin = BUILD_DIR / "payload_test.bin"
    subprocess.run([
        sys.executable, "Server/export_payload.py", "--out", str(payload_bin)
    ], check=True, cwd=ROOT)

    # 3. Build phone unsigned APK
    print("\n[3/5] Packaging unsigned APK...")
    base_apk = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"
    unsigned_apk = BUILD_DIR / "phone-unsigned.apk"
    patched_il2cpp = BUILD_DIR / "libil2cpp-arm64-patched.so"

    subprocess.run([
        sys.executable, "Server/build_phone_apk.py",
        str(base_apk), str(unsigned_apk),
        "--scheme", "http",
        "--server-host", "127.0.0.1",
        "--server-port", "8080",
        "--bundle-server",
        "--patched-il2cpp", str(patched_il2cpp)
    ], check=True, cwd=ROOT)

    # 4. Zipalign
    print("\n[4/5] Aligning APK (zipalign)...")
    aligned_apk = BUILD_DIR / "phone-aligned.apk"
    zipalign = ROOT / "toolchain" / "android-13" / "zipalign.exe"
    subprocess.run([
        str(zipalign), "-f", "-p", "4",
        str(unsigned_apk), str(aligned_apk)
    ], check=True, cwd=ROOT)

    # 5. Sign with apksigner
    print("\n[5/5] Signing APK (apksigner)...")
    apksigner = ROOT / "toolchain" / "android-13" / "apksigner.bat"
    keystore = BUILD_DIR / "debug.keystore"
    java_home = "C:\\Program Files\\Microsoft\\jdk-17.0.20.8-hotspot"
    env = os.environ.copy()
    env["JAVA_HOME"] = java_home
    env["PATH"] = f"{java_home}\\bin;{env.get('PATH', '')}"

    subprocess.run([
        str(apksigner), "sign",
        "--ks", str(keystore),
        "--ks-pass", "pass:android",
        "--out", str(output_apk_path),
        str(aligned_apk)
    ], check=True, cwd=ROOT, env=env)

    print(f"\n[OK] Successfully generated: {output_apk_path} ({output_apk_path.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    main()
