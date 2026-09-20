import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ndk_dir = ROOT / "toolchain" / "android-ndk-r26b"
if not ndk_dir.exists():
    ndk_dir = ROOT / "toolchain" / "android-ndk-r26d"
clang = ndk_dir / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"
hook_so = ROOT / "tools" / "nativehook" / "libdothook.so"
native_dir = ROOT / "tools" / "nativehook"

sources = [
    str(native_dir / "hook.c"),
    str(native_dir / "hook_quest.c"),
    str(native_dir / "hook_ui.c"),
    str(native_dir / "hook_combat.c"),
    str(native_dir / "hook_diagnostics.c"),
    str(native_dir / "inapk_server.c"),
]

print(f"Compiling {hook_so} using {clang}...")
res = subprocess.run([
    str(clang), "-shared", "-O2", "-fPIC", "-Wl,-soname,libdothook.so",
    f"-I{native_dir}",
    "-o", str(hook_so), *sources, "-llog"
], cwd=ROOT)

if res.returncode == 0:
    print(f"Success! {hook_so.stat().st_size} bytes")
else:
    print(f"Compilation failed with exit code {res.returncode}")
    sys.exit(res.returncode)
