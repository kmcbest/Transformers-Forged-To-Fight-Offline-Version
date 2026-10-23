#!/usr/bin/env python3
"""
TFTF Desktop Combat Simulator DLL Builder
========================================
Compiles sim_bridge.c + skills/dispatcher + all bot skills into sim_skills.dll.
"""
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
NDK_CLANG = REPO_ROOT / "toolchain/android-ndk-r26b/toolchains/llvm/prebuilt/windows-x86_64/bin/clang.exe"
OUTPUT_DLL = REPO_ROOT / "tools/sim/sim_skills.dll"

def build():
    if not NDK_CLANG.exists():
        print(f"[!] Clang not found at: {NDK_CLANG}")
        return False

    sources = [
        str(REPO_ROOT / "tools/sim/sim_bridge.c"),
        str(REPO_ROOT / "tools/nativehook/skills/skill_dispatcher.c"),
    ]

    skills_dir = REPO_ROOT / "tools/nativehook/skills/bots"
    for c_file in sorted(skills_dir.glob("*.c")):
        sources.append(str(c_file))

    cmd = [
        str(NDK_CLANG),
        "-shared",
        "-O2",
        "-o", str(OUTPUT_DLL),
        "-I", str(REPO_ROOT / "tools/sim/include"),
        "-I", str(REPO_ROOT / "toolchain/android-ndk-r26b/toolchains/llvm/prebuilt/windows-x86_64/lib/clang/17/include"),
        "-I", str(REPO_ROOT / "tools/nativehook/skills"),
        "-I", str(REPO_ROOT / "tools/sim"),
        "C:/Windows/System32/msvcrt.dll",
        "-nostdlib",
        "-Wl,--entry,DllMain",
    ] + sources

    print(f"[*] Building {OUTPUT_DLL.name} with {len(sources)} sources...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[!] Build FAILED!")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        return False

    print(f"[+] Build SUCCESS! Size: {OUTPUT_DLL.stat().st_size} bytes")
    return True

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
