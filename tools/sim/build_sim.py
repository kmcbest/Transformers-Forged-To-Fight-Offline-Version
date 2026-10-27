#!/usr/bin/env python3
"""
TFTF Desktop Combat Simulator DLL Builder
========================================
Compiles sim_bridge.c + skills/dispatcher + all bot skills into sim_skills.dll.
"""
import os
import sys
import time
import subprocess
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
NDK_CLANG = REPO_ROOT / "toolchain/android-ndk-r26b/toolchains/llvm/prebuilt/windows-x86_64/bin/clang.exe"
CLANG_INC = REPO_ROOT / "toolchain/android-ndk-r26b/toolchains/llvm/prebuilt/windows-x86_64/lib/clang/17/include"
if not NDK_CLANG.exists():
    NDK_CLANG = REPO_ROOT / "toolchain/android-ndk-r26d/toolchains/llvm/prebuilt/windows-x86_64/bin/clang.exe"
    CLANG_INC = REPO_ROOT / "toolchain/android-ndk-r26d/toolchains/llvm/prebuilt/windows-x86_64/lib/clang/17/include"
OUTPUT_DLL = REPO_ROOT / "tools/sim/sim_skills.dll"

def kill_existing_sim_server():
    """Kill any existing sim_server.py process to release DLL file lock and port 8088."""
    current_pid = os.getpid()
    parent_pid = os.getppid() if hasattr(os, 'getppid') else 0
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            pid = proc.info.get('pid')
            if pid in (current_pid, parent_pid):
                continue
            cmdline = proc.info.get('cmdline') or []
            cmd_str = " ".join(cmdline).lower()
            if "sim_server.py" in cmd_str:
                print(f"[*] 检测到旧模拟器服务进程 (PID: {pid})，正在关闭以释放 DLL 锁与端口 8088...")
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                except Exception:
                    pass
    except Exception:
        pass

def prepare_output_file():
    """Ensure OUTPUT_DLL can be written by linker, freeing locks or renaming if necessary."""
    for old_file in OUTPUT_DLL.parent.glob("sim_skills_*.old"):
        try:
            old_file.unlink()
        except Exception:
            pass

    if not OUTPUT_DLL.exists():
        return

    try:
        with open(OUTPUT_DLL, "a+b") as f:
            pass
    except (PermissionError, OSError):
        print("[*] 检测到 sim_skills.dll 正被运行中的模拟器占用，正在自动释放...")
        kill_existing_sim_server()
        time.sleep(0.3)
        try:
            with open(OUTPUT_DLL, "a+b") as f:
                pass
            print("[+] 文件锁已成功释放。")
        except (PermissionError, OSError):
            backup = OUTPUT_DLL.with_name(f"sim_skills_{int(time.time())}.old")
            try:
                OUTPUT_DLL.rename(backup)
                print(f"[+] 已将占用文件临时移位为 {backup.name}，可安全编译新库。")
            except Exception as e:
                print(f"[!] 无法重命名被占用 DLL: {e}")

def build():
    if not NDK_CLANG.exists():
        print(f"[!] Clang not found at: {NDK_CLANG}")
        return False

    prepare_output_file()

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
        "-I", str(CLANG_INC),
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
