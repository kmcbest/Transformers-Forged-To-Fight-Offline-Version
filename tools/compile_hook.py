#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ndk_dir = ROOT / "toolchain" / "android-ndk-r26d"
if not ndk_dir.exists():
    ndk_dir = ROOT / "toolchain" / "android-ndk-r26b"
clang = ndk_dir / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"
hook_so = ROOT / "tools" / "nativehook" / "libdothook.so"

sources = [
    str(ROOT / "tools" / "nativehook" / "hook.c"),
    str(ROOT / "tools" / "nativehook" / "inapk_server.c"),
]
skills_dir = ROOT / "tools" / "nativehook" / "skills"
if skills_dir.exists():
    for c_file in sorted(skills_dir.rglob("*.c")):
        sources.append(str(c_file))

print(f"Clang: {clang}")
print(f"Hook SO target: {hook_so}")

cmd = [
    str(clang), "-shared", "-O2", "-fPIC", "-Wl,-soname,libdothook.so",
    "-o", str(hook_so)
] + sources + ["-llog"]

res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
print(f"Exit code: {res.returncode}")
if res.returncode == 0:
    print(f"Success! Output size: {hook_so.stat().st_size} bytes")
else:
    sys.exit(res.returncode)
