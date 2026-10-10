#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ndk_dir = ROOT / "toolchain" / "android-ndk-r26d"
clang = ndk_dir / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"
hook_so = ROOT / "tools" / "nativehook" / "libdothook.so"
hook_c = ROOT / "tools" / "nativehook" / "hook.c"
inapk_server_c = ROOT / "tools" / "nativehook" / "inapk_server.c"

print(f"Clang: {clang}")
print(f"Hook SO target: {hook_so}")

cmd = [
    str(clang), "-shared", "-O2", "-fPIC", "-Wl,-soname,libdothook.so",
    "-o", str(hook_so), str(hook_c), str(inapk_server_c), "-llog"
]

res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
print(f"Exit code: {res.returncode}")
if res.returncode == 0:
    print(f"Success! Output size: {hook_so.stat().st_size} bytes")
else:
    sys.exit(res.returncode)
