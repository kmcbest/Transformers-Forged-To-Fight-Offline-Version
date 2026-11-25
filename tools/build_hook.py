import argparse
import subprocess
import sys
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument("--autotest", action="store_true", help="Build with -DTFTF_AUTOTEST=1 into libdothook-autotest.so")
args = parser.parse_args()

ROOT_DIR = Path(__file__).resolve().parent.parent
ndk_clang = ROOT_DIR / "toolchain" / "android-ndk-r26b" / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"
if not ndk_clang.exists():
    ndk_clang = ROOT_DIR / "toolchain" / "android-ndk-r26d" / "toolchains" / "llvm" / "prebuilt" / "windows-x86_64" / "bin" / "aarch64-linux-android28-clang.cmd"

out_name = "libdothook-autotest.so" if args.autotest else "libdothook.so"
out_so = ROOT_DIR / "tools" / "nativehook" / out_name

sources = [
    str(ROOT_DIR / "tools" / "nativehook" / "hook.c"),
    str(ROOT_DIR / "tools" / "nativehook" / "inapk_server.c"),
    str(ROOT_DIR / "tools" / "nativehook" / "inapk_pvp.c"),
    str(ROOT_DIR / "tools" / "nativehook" / "autotest.c"),
]
skills_dir = ROOT_DIR / "tools" / "nativehook" / "skills"
if skills_dir.exists():
    for c_file in sorted(skills_dir.rglob("*.c")):
        sources.append(str(c_file))

defines = ["-DTFTF_AUTOTEST=1"] if args.autotest else []

cmd = [
    str(ndk_clang),
    "-shared",
    "-O2",
    "-fPIC",
    "-Wl,-soname,libdothook.so",
] + defines + [
    "-o", str(out_so),
] + sources + ["-llog"]

print("Running build with", len(sources), "source files...")
res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
if res.returncode == 0:
    print(f"Build succeeded! Size: {out_so.stat().st_size} bytes")
else:
    print("Build failed with code:", res.returncode)
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    sys.exit(res.returncode)
