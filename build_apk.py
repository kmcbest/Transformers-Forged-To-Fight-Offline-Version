#!/usr/bin/env python3
"""Build and sign offline APK for Transformers Forged to Fight.
Dynamically sets output APK name based on current git branch.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
BUILD_DIR.mkdir(exist_ok=True)
OUT_DIR = (BUILD_DIR / "out").resolve()
OUT_DIR.mkdir(exist_ok=True)

def sync_tools_to_out(out_dir: Path, root: Path) -> tuple[Path, Path]:
    """Sync zipalign and apksigner (~2MB) to C: SSD out/.tools to ensure 100% silent, zero-HDD steps 4 & 5."""
    tools_dir = out_dir / ".tools"
    tools_dir.mkdir(exist_ok=True)
    (tools_dir / "lib").mkdir(exist_ok=True)

    candidates = [
        root / "toolchain" / "android-13",
        root / "toolchain" / "android-sdk" / "build-tools" / "34.0.0",
        root / "toolchain" / "android-sdk" / "build-tools" / "36.0.0",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "build-tools" / "34.0.0",
        Path("D:/Android/Sdk/build-tools/36.0.0"),
    ]
    src_bt = None
    for cand in candidates:
        if (cand / "zipalign.exe").exists():
            src_bt = cand
            break
    if src_bt is None:
        found = list((root / "toolchain").glob("**/zipalign.exe"))
        if found:
            src_bt = found[0].parent
        else:
            raise FileNotFoundError("Could not find Android build-tools with zipalign.exe")

    for fname in ["zipalign.exe", "apksigner.bat"]:
        sf = src_bt / fname
        df = tools_dir / fname
        if sf.exists() and (not df.exists() or df.stat().st_size != sf.stat().st_size):
            shutil.copy2(sf, df)

    sf_jar = src_bt / "lib" / "apksigner.jar"
    df_jar = tools_dir / "lib" / "apksigner.jar"
    if sf_jar.exists() and (not df_jar.exists() or df_jar.stat().st_size != sf_jar.stat().st_size):
        shutil.copy2(sf_jar, df_jar)

    zipalign = tools_dir / "zipalign.exe" if (tools_dir / "zipalign.exe").exists() else (src_bt / "zipalign.exe")
    apksigner = tools_dir / "apksigner.bat" if (tools_dir / "apksigner.bat").exists() else (src_bt / "apksigner.bat")
    return zipalign, apksigner

def get_git_branch() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
           #heck=True
        )
        branch = res.stdout.strip().replace("/", "-")
        return branch if branch else "custom"
    except Exception:
        return "custom"


def main():
    branch = get_git_branch()
    if branch == "redeco":
        output_apk_name = "Transformers-9.2-offline-redeco-edition.apk"
    else:
        output_apk_name = f'Transformers-9.2-offline-{branch}.apk'
    output_apk_path = OUT_DIR / output_apk_name
    print(f"=== Building Offline APK for branch [{branch}] ===")
    print(f"Target APK: {output_apk_path}")

    # 1. Compile native hook
    print("\n[1/5] Compiling libdothook.so...")
    subprocess.run([sys.executable, "tools/build_hook.py"], check=True, cwd=ROOT)

    # 2. Export offline payload
    print("\n[2/5] Regenerating responses and exporting offline payload...")
    subprocess.run([sys.executable, "Server/gamedata.py"], check=True, cwd=ROOT)
    payload_bin = BUILD_DIR / "payload_test.bin"
    subprocess.run([
        sys.executable, "Server/export_payload.py", "--out", str(payload_bin)
    ], check=True, cwd=ROOT)

    # 2.5. Build launcher DEX
    print("\n[2.5/5] Building launcher DEX (classes3.dex)...")
    subprocess.run([
        sys.executable, "tools/build_launcher_dex.py", str(BUILD_DIR / "classes3.dex")
    ], check=True, cwd=ROOT)

    # 3. Build phone unsigned APK
    print("\n[3/5] Packaging unsigned APK...")
    base_apk = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"
    unsigned_apk = OUT_DIR / "phone-unsigned.apk"
    patched_il2cpp = BUILD_DIR / "libil2cpp-arm64-patched.so"

    subprocess.run([
        sys.executable, "Server/build_phone_apk.py",
        str(base_apk), str(unsigned_apk),
        "--scheme", "http",
        "--server-host", "127.0.0.1",
        "--server-port", "8080",
        "--bundle-server",
        "--payload-bin", str(payload_bin),
        "--patched-il2cpp", str(patched_il2cpp)
    ], check=True, cwd=ROOT)

    # Prepare tools and keystore on C: SSD to ensure 100% silent, zero-HDD steps 4 & 5
    zipalign, apksigner = sync_tools_to_out(OUT_DIR, ROOT)
    keystore = OUT_DIR / "debug.keystore"
    src_ks = BUILD_DIR / "debug.keystore"
    if src_ks.exists() and (not keystore.exists() or keystore.stat().st_size != src_ks.stat().st_size):
        shutil.copy2(src_ks, keystore)

    # 4. Zipalign
    print("\n[4/5] Aligning APK (zipalign)...")
    aligned_apk = OUT_DIR / "phone-aligned.apk"
    subprocess.run([
        str(zipalign), "-f", "-p", "4",
        str(unsigned_apk), str(aligned_apk)
    ], check=True, cwd=OUT_DIR)

    # 5. Sign with apksigner
    print("\n[5/5] Signing APK (apksigner)...")
    env = os.environ.copy()
    # Prioritize C: SSD JDK to prevent HDD random I/O during JVM startup
    jdk_candidates = [
        Path("C:/Program Files/Java/jdk-17"),
        Path("C:/Program Files/Microsoft/jdk-17.0.20.8-hotspot"),
        ROOT / "toolchain" / "jdk-21",
        ROOT / "toolchain" / "jdk-17",
    ]
    for cand in jdk_candidates:
        if cand.exists():
            env["JAVA_HOME"] = str(cand)
            env["PATH"] = f"{cand}\\bin;{env.get('PATH', '')}"
            break

    subprocess.run([
        str(apksigner), "sign",
        "--ks", str(keystore),
        "--ks-pass", "pass:android",
        "--out", str(output_apk_path),
        str(aligned_apk)
    ], check=True, cwd=OUT_DIR, env=env)

    # 6. Clean up temporary unsigned and aligned APKs
    print("\n[6/6] Cleaning up temporary APK files...")
    unsigned_apk.unlink(missing_ok=True)
    aligned_apk.unlink(missing_ok=True)
    for p in OUT_DIR.glob("*unsigned*.apk"):
        p.unlink(missing_ok=True)
    for p in OUT_DIR.glob("*aligned*.apk"):
        p.unlink(missing_ok=True)
    for p in BUILD_DIR.glob("*unsigned*.apk"):
        p.unlink(missing_ok=True)
    for p in BUILD_DIR.glob("*aligned*.apk"):
        p.unlink(missing_ok=True)

    print(f"\n[OK] Successfully generated: {output_apk_path} ({output_apk_path.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    main()
