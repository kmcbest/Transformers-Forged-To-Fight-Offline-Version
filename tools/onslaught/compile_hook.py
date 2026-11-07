import subprocess
from pathlib import Path

root = Path(r"E:\Agent\TFTF-blender")
ndk_dir = root / "toolchain" / "android-ndk-r26b"
if not ndk_dir.exists():
    ndk_dir = root / "toolchain" / "android-ndk-r26d"
clang = ndk_dir / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"
hook_so = root / "tools" / "nativehook" / "libdothook.so"
hook_c = root / "tools" / "nativehook" / "hook.c"
inapk_server_c = root / "tools" / "nativehook" / "inapk_server.c"

print("Compiling libdothook.so...")
cmd = [
    str(clang), "-shared", "-O2", "-fPIC", "-Wl,-soname,libdothook.so",
    "-o", str(hook_so), str(hook_c), str(inapk_server_c), "-llog"
]
res = subprocess.run(cmd, cwd=root)
print(f"Exit code: {res.returncode}")
if res.returncode == 0:
    print(f"Successfully compiled libdothook.so ({hook_so.stat().st_size} bytes)!")
