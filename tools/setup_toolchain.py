# -*- coding: utf-8 -*-
"""
Setup toolchain for TFTF 3D model adaptation pipeline.
Installs Blender 3.6 LTS, Unity Hub, and Unity 2020.3.31f1 (with Android support)
into e:\Agent\TFTF-blender\toolchain without touching C: drive.
"""
import sys
import os
import shutil
import zipfile
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
TOOLCHAIN_DIR = ROOT_DIR / "toolchain"
DOWNLOADS_DIR = TOOLCHAIN_DIR / "downloads"

BLENDER_DIR = TOOLCHAIN_DIR / "blender"
UNITY_HUB_DIR = TOOLCHAIN_DIR / "UnityHub"
UNITY_DIR = TOOLCHAIN_DIR / "Unity_2020.3.31f1"

DOWNLOADS = {
    "blender": {
        "url": "https://mirrors.tuna.tsinghua.edu.cn/blender/release/Blender3.6/blender-3.6.23-windows-x64.zip",
        "file": DOWNLOADS_DIR / "blender-3.6.23-windows-x64.zip",
        "expected_min_size": 350 * 1024 * 1024,
    },
    "unity_hub": {
        "url": "https://public-cdn.cloud.unitychina.cn/hub/prod/UnityHubSetup.exe",
        "file": DOWNLOADS_DIR / "UnityHubSetup.exe",
        "expected_min_size": 100 * 1024 * 1024,
    },
    "unity_editor": {
        "url": "https://download.unitychina.cn/download_unity/6b54b7616050/Windows64EditorInstaller/UnitySetup64-2020.3.31f1.exe",
        "file": DOWNLOADS_DIR / "UnitySetup64-2020.3.31f1.exe",
        "expected_min_size": 2500 * 1024 * 1024,
    },
    "unity_android": {
        "url": "https://download.unitychina.cn/download_unity/6b54b7616050/TargetSupportInstaller/UnitySetup-Android-Support-for-Editor-2020.3.31f1.exe",
        "file": DOWNLOADS_DIR / "UnitySetup-Android-Support-for-Editor-2020.3.31f1.exe",
        "expected_min_size": 350 * 1024 * 1024,
    },
}

def download_file(name, item):
    dest = item["file"]
    if dest.exists() and dest.stat().st_size >= item["expected_min_size"]:
        print(f"[✓] {name} already downloaded: {dest} ({dest.stat().st_size / (1024*1024):.1f} MB)")
        return True
    
    print(f"[*] Downloading {name} from {item['url']}...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Use curl with resume support
    cmd = ["curl.exe", "-L", "-C", "-", "--retry", "3", "-o", str(dest), item["url"]]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[!] Failed to download {name}")
        return False
    print(f"[✓] Successfully downloaded {name}: ({dest.stat().st_size / (1024*1024):.1f} MB)")
    return True

def install_blender():
    blender_exe = BLENDER_DIR / "blender.exe"
    if blender_exe.exists():
        print(f"[✓] Blender already installed at: {blender_exe}")
        return True
    
    zip_path = DOWNLOADS["blender"]["file"]
    if not zip_path.exists():
        print(f"[!] Blender zip not found: {zip_path}")
        return False
    
    print(f"[*] Extracting Blender to {BLENDER_DIR}...")
    BLENDER_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Determine root folder in zip
        members = zf.namelist()
        top_dirs = set(m.split('/')[0] for m in members if '/' in m)
        if len(top_dirs) == 1:
            top_dir = list(top_dirs)[0]
            print(f"[*] Extracting from inner dir: {top_dir}...")
            # Extract to temporary or directly
            for member in members:
                # Strip top dir
                rel_path = member[len(top_dir)+1:]
                if not rel_path:
                    continue
                target_path = BLENDER_DIR / rel_path
                if member.endswith('/'):
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
        else:
            zf.extractall(BLENDER_DIR)
            
    if blender_exe.exists():
        print(f"[✓] Blender installed successfully: {blender_exe}")
        return True
    else:
        print(f"[!] Blender executable not found at: {blender_exe}")
        return False

def install_unity_hub():
    hub_exe = UNITY_HUB_DIR / "Unity Hub.exe"
    if hub_exe.exists():
        print(f"[✓] Unity Hub already installed at: {hub_exe}")
        return True
        
    installer = DOWNLOADS["unity_hub"]["file"]
    if not installer.exists():
        print(f"[!] Unity Hub installer not found: {installer}")
        return False
        
    print(f"[*] Silently installing Unity Hub to {UNITY_HUB_DIR}...")
    UNITY_HUB_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [str(installer), "/S", f"/D={UNITY_HUB_DIR}"]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[!] Unity Hub installer exited with code {res.returncode}")
        return False
        
    if hub_exe.exists():
        print(f"[✓] Unity Hub installed successfully: {hub_exe}")
        return True
    else:
        print(f"[!] Unity Hub executable not found at: {hub_exe}")
        return False

def install_unity_editor():
    unity_exe = UNITY_DIR / "Editor" / "Unity.exe"
    if unity_exe.exists():
        print(f"[✓] Unity Editor already installed at: {unity_exe}")
    else:
        installer = DOWNLOADS["unity_editor"]["file"]
        if not installer.exists():
            print(f"[!] Unity Editor installer not found: {installer}")
            return False
            
        print(f"[*] Silently installing Unity Editor 2020.3.31f1 to {UNITY_DIR}...")
        UNITY_DIR.mkdir(parents=True, exist_ok=True)
        cmd = [str(installer), "/S", f"/D={UNITY_DIR}"]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"[!] Unity Editor installer exited with code {res.returncode}")
            return False

    # Install Android Support
    android_player = UNITY_DIR / "Editor" / "Data" / "PlaybackEngines" / "AndroidPlayer"
    if android_player.exists():
        print(f"[✓] Unity Android Support already installed at: {android_player}")
        return True
        
    installer_android = DOWNLOADS["unity_android"]["file"]
    if not installer_android.exists():
        print(f"[!] Unity Android Support installer not found: {installer_android}")
        return False
        
    print(f"[*] Silently installing Unity Android Support to {UNITY_DIR}...")
    cmd_android = [str(installer_android), "/S", f"/D={UNITY_DIR}"]
    res_android = subprocess.run(cmd_android)
    if res_android.returncode != 0:
        print(f"[!] Unity Android installer exited with code {res_android.returncode}")
        return False

    if android_player.exists():
        print(f"[✓] Unity Android Support installed successfully: {android_player}")
        return True
    else:
        print(f"[!] AndroidPlayer not found at: {android_player}")
        return False

def verify_all():
    print("\n=== Verifying Installed Toolchain ===")
    # Blender
    blender_exe = BLENDER_DIR / "blender.exe"
    if blender_exe.exists():
        res = subprocess.run([str(blender_exe), "-b", "--version"], capture_output=True, text=True)
        print(f"[✓] Blender headless test:\n    {res.stdout.splitlines()[0] if res.stdout else 'OK'}")
    else:
        print(f"[✗] Blender missing: {blender_exe}")
        
    # Unity Hub
    hub_exe = UNITY_HUB_DIR / "Unity Hub.exe"
    if hub_exe.exists():
        print(f"[✓] Unity Hub binary present: {hub_exe}")
    else:
        print(f"[✗] Unity Hub missing: {hub_exe}")
        
    # Unity Editor
    unity_exe = UNITY_DIR / "Editor" / "Unity.exe"
    if unity_exe.exists():
        res = subprocess.run([str(unity_exe), "-batchmode", "-quit", "-version"], capture_output=True, text=True)
        print(f"[✓] Unity Editor headless test:\n    {res.stdout.strip() if res.stdout else 'OK'}")
    else:
        print(f"[✗] Unity Editor missing: {unity_exe}")
        
    # Android Support
    android_player = UNITY_DIR / "Editor" / "Data" / "PlaybackEngines" / "AndroidPlayer"
    if android_player.exists():
        print(f"[✓] Unity Android Build Support present: {android_player}")
    else:
        print(f"[✗] Android Build Support missing: {android_player}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"Toolchain target dir: {TOOLCHAIN_DIR}")
    
    if mode in ("all", "download"):
        for name, item in DOWNLOADS.items():
            if not download_file(name, item):
                sys.exit(1)
                
    if mode in ("all", "install"):
        print("\n=== Installing Toolchain Components ===")
        if not install_blender():
            print("[!] Blender installation failed")
        if not install_unity_hub():
            print("[!] Unity Hub installation failed")
        if not install_unity_editor():
            print("[!] Unity Editor installation failed")
            
    if mode in ("all", "verify"):
        verify_all()
