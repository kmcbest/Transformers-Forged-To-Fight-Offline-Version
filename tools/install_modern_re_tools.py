"""
One-click installer for Modern Reverse Engineering Toolchain in TFTF.
Installs entirely on E:\\Agent\\TFTF\\toolchain without polluting C: drive.
Creates directory junctions in C:\\Tools for convenience.
"""

import os
import sys
import time
import urllib.request
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF\toolchain").resolve()
DOWNLOADS_DIR = BASE_DIR / "downloads"
JDK_DIR = BASE_DIR / "jdk-21"
GHIDRA_DIR = BASE_DIR / "ghidra"
JADX_DIR = BASE_DIR / "jadx"
DUMPER_DIR = BASE_DIR / "Il2CppDumper"
REA_DIR = BASE_DIR / "rea"

def download_file(url, dest_path):
    if dest_path.exists() and dest_path.stat().st_size > 0:
        print(f"[+] {dest_path.name} already downloaded ({dest_path.stat().st_size / (1024*1024):.2f} MB). Skipping download.")
        return

    print(f"[*] Downloading {url} -> {dest_path}...")
    temp_path = dest_path.with_suffix(".tmp")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    t0 = time.time()
    last_print = t0

    with urllib.request.urlopen(req) as resp, open(temp_path, "wb") as f:
        total = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        chunk_size = 1024 * 512
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_print > 1.0 or downloaded == total:
                elapsed = max(now - t0, 0.001)
                speed = downloaded / (1024 * 1024) / elapsed
                percent = (downloaded / total * 100) if total else 0
                print(f"\r    {downloaded / (1024*1024):.1f}MB / {total / (1024*1024):.1f}MB ({percent:.1f}%) @ {speed:.2f} MB/s", end="", flush=True)
                last_print = now
    print()
    if dest_path.exists():
        dest_path.unlink()
    temp_path.replace(dest_path)
    print(f"[+] Download complete: {dest_path.name}")

def extract_archive(archive_path, output_dir):
    print(f"[*] Extracting {archive_path.name} -> {output_dir}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["7z", "x", "-y", f"-o{output_dir}", str(archive_path)]
    subprocess.check_call(cmd)
    print(f"[+] Extraction complete for {archive_path.name}")

def make_junction(link_path, target_path):
    if not link_path.exists():
        link_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["cmd", "/c", f"mklink /J \"{link_path}\" \"{target_path}\""], check=True)
            print(f"[+] Junction created: {link_path} -> {target_path}")
        except Exception as e:
            print(f"[!] Warning creating junction {link_path}: {e}")

def main():
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. JADX
    jadx_check = JADX_DIR / "bin" / "jadx.bat"
    if not jadx_check.exists():
        zip_path = DOWNLOADS_DIR / "jadx-1.5.6.zip"
        download_file("https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip", zip_path)
        extract_archive(zip_path, JADX_DIR)
    print(f"[+] JADX ready at {JADX_DIR}")

    # 2. Il2CppDumper
    dumper_check = DUMPER_DIR / "Il2CppDumper.exe"
    if not dumper_check.exists():
        zip_path = DOWNLOADS_DIR / "Il2CppDumper-win-v6.7.46.zip"
        download_file("https://github.com/Perfare/Il2CppDumper/releases/download/v6.7.46/Il2CppDumper-win-v6.7.46.zip", zip_path)
        extract_archive(zip_path, DUMPER_DIR)
    print(f"[+] Il2CppDumper ready at {DUMPER_DIR}")

    # 3. Adoptium OpenJDK 21
    jdk_check = JDK_DIR / "bin" / "java.exe"
    if not jdk_check.exists():
        zip_path = DOWNLOADS_DIR / "OpenJDK21U-jdk_x64_windows_hotspot.zip"
        api_url = "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            download_url = resp.geturl()
        download_file(download_url, zip_path)
        temp_dir = BASE_DIR / "jdk21_tmp"
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        extract_archive(zip_path, temp_dir)
        subdirs = [p for p in temp_dir.iterdir() if p.is_dir()]
        if subdirs:
            if JDK_DIR.exists(): shutil.rmtree(JDK_DIR)
            shutil.move(str(subdirs[0]), str(JDK_DIR))
            shutil.rmtree(temp_dir)
    print(f"[+] JDK 21 ready at {JDK_DIR}")

    # 4. Ghidra
    ghidra_check = GHIDRA_DIR / "ghidraRun.bat"
    if not ghidra_check.exists():
        zip_path = DOWNLOADS_DIR / "ghidra_12.1.4_PUBLIC_20260921.zip"
        download_file("https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip", zip_path)
        temp_dir = BASE_DIR / "ghidra_tmp"
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        extract_archive(zip_path, temp_dir)
        subdirs = [p for p in temp_dir.iterdir() if p.is_dir()]
        if subdirs:
            if GHIDRA_DIR.exists(): shutil.rmtree(GHIDRA_DIR)
            shutil.move(str(subdirs[0]), str(GHIDRA_DIR))
            shutil.rmtree(temp_dir)
    # Configure JAVA_HOME_OVERRIDE in launch.properties
    launch_prop = GHIDRA_DIR / "support" / "launch.properties"
    if launch_prop.exists():
        with open(launch_prop, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.startswith("JAVA_HOME_OVERRIDE="):
                new_lines.append(f"JAVA_HOME_OVERRIDE={str(JDK_DIR).replace(os.sep, '/')}\n")
            else:
                new_lines.append(line)
        with open(launch_prop, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    print(f"[+] Ghidra ready at {GHIDRA_DIR} (configured with portable JDK 21)")

    # 5. REA
    rea_check = REA_DIR / "node_modules" / "rea-agents" / "scripts" / "rea.mjs"
    if not rea_check.exists():
        REA_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["npm", "init", "-y"], cwd=str(REA_DIR), check=True)
        subprocess.run(["npm", "install", "rea-agents@latest"], cwd=str(REA_DIR), check=True)
    print(f"[+] REA ready at {REA_DIR}")

    # 6. Junctions in C:\Tools
    c_tools = Path(r"C:\Tools")
    make_junction(c_tools / "ghidra", GHIDRA_DIR)
    make_junction(c_tools / "jadx", JADX_DIR)
    make_junction(c_tools / "Il2CppDumper", DUMPER_DIR)
    make_junction(c_tools / "rea", REA_DIR)
    make_junction(c_tools / "jdk-21", JDK_DIR)

    print("\n[+] Modern Reverse Engineering Toolchain fully verified and ready!")

if __name__ == "__main__":
    main()
