import subprocess
from pathlib import Path

ndk_clang = Path("toolchain/android-ndk-r26b/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android28-clang.cmd")
if not ndk_clang.exists():
    ndk_clang = Path("toolchain/android-ndk-r26d/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android28-clang.cmd")

sources = [
    "tools/nativehook/hook.c",
    "tools/nativehook/inapk_server.c",
    "tools/nativehook/inapk_pvp.c",
]
skills_dir = Path("tools/nativehook/skills")
if skills_dir.exists():
    for c_file in sorted(skills_dir.rglob("*.c")):
        sources.append(str(c_file).replace("\\", "/"))

cmd = [
    str(ndk_clang),
    "-shared",
    "-O2",
    "-fPIC",
    "-Wl,-soname,libdothook.so",
    "-o", "tools/nativehook/libdothook.so",
] + sources + ["-llog"]

print("Running build:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
if res.returncode == 0:
    so_path = Path("tools/nativehook/libdothook.so")
    print(f"Build succeeded! Size: {so_path.stat().st_size} bytes")
else:
    print("Build failed with code:", res.returncode)
    import sys
    sys.exit(res.returncode)
