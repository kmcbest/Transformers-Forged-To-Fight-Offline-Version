import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ndk_dir = ROOT / "toolchain" / "android-ndk-r26b"
if not ndk_dir.exists():
    ndk_dir = ROOT / "toolchain" / "android-ndk-r26d"

clang = ndk_dir / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"
hook_so = ROOT / "tools" / "nativehook" / "libdothook.so"
hook_c = ROOT / "tools" / "nativehook" / "hook.c"
inapk_server_c = ROOT / "tools" / "nativehook" / "inapk_server.c"

cmd = [
    str(clang), "-shared", "-O2", "-fPIC", "-Wl,-soname,libdothook.so",
    "-o", str(hook_so), str(hook_c), str(inapk_server_c), "-llog"
]
print(f"Compiling {hook_so}...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print("Compilation FAILED:")
    print(res.stderr)
    exit(1)
else:
    print(f"Success! {hook_so.stat().st_size} bytes")
