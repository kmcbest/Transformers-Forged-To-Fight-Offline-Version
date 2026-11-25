#!/usr/bin/env python3
"""
Fast 1-second hot-deploy helper for MuMu Player 15 / rooted Android emulators.

Rebuilds libdothook-autotest.so (`tools/build_hook.py --autotest`) and the
offline Server payload (`Server/export_payload.py --out build/payload_test.bin`),
then pushes BOTH directly to the emulator without rebuilding or reinstalling the
1.4 GB APK:
  - libdothook-autotest.so -> <app_arm64_libdir>/libdothook.so (fresh inode!)
  - build/payload_test.bin -> /sdcard/Android/data/com.kabam.bigrobot/files/tftf_offline_payload.bin

Requires the autotest APK already installed with `adb install -r --no-incremental`.
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PKG = "com.kabam.bigrobot"
ACTIVITY = f"{PKG}/com.explodingbarrel.Activity"
HOT_PAYLOAD_REMOTE = f"/sdcard/Android/data/{PKG}/files/tftf_offline_payload.bin"


def find_adb(repo_root: Path) -> str:
    for cand in [
        str(repo_root / "toolchain/android-sdk/platform-tools/adb.exe"),
        shutil.which("adb"),
        "D:/Android/Sdk/platform-tools/adb.exe",
        str(Path.home() / "Android/Sdk/platform-tools/adb.exe"),
    ]:
        if cand and Path(cand).exists():
            return str(cand)
    raise FileNotFoundError("adb.exe not found in repo toolchain, PATH, or standard SDK locations")


def run_step(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )


def adb_cmd(adb: str, serial: str | None, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [adb]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def ensure_connected_and_root(adb: str, serial: str | None) -> str:
    """Connect (for TCP serials like 127.0.0.1:7555), switch adbd to root if supported, and return shell mode ('direct' or 'su')."""
    if serial and ":" in serial:
        adb_cmd(adb, None, "connect", serial, check=False)
    adb_cmd(adb, serial, "wait-for-device")

    uid_res = adb_cmd(adb, serial, "shell", "id -u", check=False)
    if uid_res.stdout.strip() == "0":
        return "direct"

    adb_cmd(adb, serial, "root", check=False)
    time.sleep(0.8)
    if serial and ":" in serial:
        adb_cmd(adb, None, "connect", serial, check=False)
    adb_cmd(adb, serial, "wait-for-device")

    uid_res = adb_cmd(adb, serial, "shell", "id -u", check=False)
    if uid_res.stdout.strip() == "0":
        return "direct"

    su_res = adb_cmd(adb, serial, "shell", "su 0 id -u", check=False)
    if su_res.stdout.strip() == "0":
        return "su"

    raise RuntimeError(
        f"Root unavailable on {serial or 'default device'} (id -u={uid_res.stdout.strip()!r}, su={su_res.stderr.strip()!r}). "
        "Enable Root permission in MuMu settings or verify adb root."
    )


def run_root_shell(adb: str, serial: str | None, shell_mode: str, script: str, check: bool = True) -> subprocess.CompletedProcess:
    if shell_mode == "direct":
        return adb_cmd(adb, serial, "shell", script, check=check)
    escaped = script.replace("'", "'\\''")
    return adb_cmd(adb, serial, "shell", f"su 0 sh -c '{escaped}'", check=check)


def deploy_to_device(
    repo_root: Path,
    serial: str | None = "127.0.0.1:7555",
    build_so: bool = True,
    push_so: bool = True,
    build_payload: bool = True,
    push_payload: bool = True,
    launch: bool = False,
) -> int:
    t0 = time.time()

    so_path = repo_root / "tools" / "nativehook" / "libdothook-autotest.so"
    if push_so and build_so:
        print("[1/4] Building libdothook-autotest.so ...")
        res = run_step([sys.executable, "tools/build_hook.py", "--autotest"], repo_root, check=False)
        if res.returncode != 0:
            print(res.stdout)
            print(res.stderr)
            return res.returncode
        print(f"      -> built {so_path.name} ({so_path.stat().st_size:,} bytes)")
    elif push_so and not so_path.exists():
        print(f"[!] Missing {so_path}; cannot skip build when file does not exist.")
        return 1

    payload_path = repo_root / "build" / "payload_test.bin"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    if push_payload and build_payload:
        print("[2/4] Exporting offline payload (build/payload_test.bin) ...")
        res = run_step([sys.executable, "Server/export_payload.py", "--out", str(payload_path)], repo_root, check=False)
        if res.returncode != 0:
            print(res.stdout)
            print(res.stderr)
            return res.returncode
        for ln in res.stdout.strip().splitlines():
            print(f"      -> {ln}")
    elif push_payload and not payload_path.exists():
        print(f"[!] Missing {payload_path}; cannot skip payload export when file does not exist.")
        return 1

    adb = find_adb(repo_root)
    print(f"[3/4] Connecting & ensuring root on {serial or 'default device'} (adb={adb}) ...")
    shell_mode = ensure_connected_and_root(adb, serial)
    print(f"      -> root active (mode={shell_mode})")

    adb_cmd(adb, serial, "shell", "am", "force-stop", PKG, check=False)

    if push_so:
        find_res = run_root_shell(
            adb,
            serial,
            shell_mode,
            f"find /data/app -type d -name arm64 2>/dev/null | grep {PKG} | head -n 1",
            check=False,
        )
        libdir = find_res.stdout.strip().splitlines()[0].strip() if find_res.stdout.strip() else ""
        if not libdir:
            print(f"[!] Could not locate /data/app/.../{PKG}-.../lib/arm64. Is the APK installed?")
            return 1

        tmp_so = "/data/local/tmp/libdothook.so"
        target_so = f"{libdir}/libdothook.so"
        push_res = adb_cmd(adb, serial, "push", str(so_path), tmp_so, check=False)
        if push_res.returncode != 0:
            print(push_res.stdout, push_res.stderr)
            return push_res.returncode

        swap_cmd = (
            f"rm -f '{target_so}' && "
            f"cp '{tmp_so}' '{target_so}' && "
            f"chown system:system '{target_so}' && "
            f"chmod 755 '{target_so}' && "
            f"(restorecon '{target_so}' 2>/dev/null || true) && "
            f"rm -f '{tmp_so}' && "
            f"ls -li '{target_so}'"
        )
        swap_res = run_root_shell(adb, serial, shell_mode, swap_cmd, check=False)
        if swap_res.returncode != 0:
            print(f"[!] Failed to hot-swap {target_so}:")
            print(swap_res.stdout)
            print(swap_res.stderr)
            print("    Hint: verify APK was installed with `adb install -r --no-incremental`.")
            return swap_res.returncode
        print(f"      -> .so hot-swapped: {swap_res.stdout.strip()}")

    if push_payload:
        adb_cmd(adb, serial, "shell", "mkdir", "-p", f"/sdcard/Android/data/{PKG}/files", check=False)
        p_res = adb_cmd(adb, serial, "push", str(payload_path), HOT_PAYLOAD_REMOTE, check=False)
        if p_res.returncode != 0:
            print(p_res.stdout, p_res.stderr)
            return p_res.returncode
        print(f"      -> payload pushed: {HOT_PAYLOAD_REMOTE} ({payload_path.stat().st_size:,} bytes)")

    if launch:
        print(f"[4/4] Launching {ACTIVITY} ...")
        adb_cmd(adb, serial, "shell", "am", "start", "-n", ACTIVITY)
    else:
        print("[4/4] Hot-deploy complete (app stopped, ready for run_autotest.py).")

    print(f"[PASS] Hot-deploy finished in {time.time() - t0:.2f}s (no APK rebuild needed).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast hot-deploy of libdothook-autotest.so and offline payload to MuMu 15")
    parser.add_argument("--serial", type=str, default="127.0.0.1:7555", help="ADB serial (default: 127.0.0.1:7555)")
    parser.add_argument("--skip-build", action="store_true", help="Skip recompiling libdothook-autotest.so")
    parser.add_argument("--skip-payload", action="store_true", help="Skip rebuilding & pushing payload_test.bin")
    parser.add_argument("--so-only", action="store_true", help="Only build & push libdothook-autotest.so")
    parser.add_argument("--payload-only", action="store_true", help="Only build & push tftf_offline_payload.bin")
    parser.add_argument("--launch", action="store_true", help="Launch the game after deploying")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    push_so = not args.payload_only
    push_payload = (not args.so_only) and (not args.skip_payload or args.payload_only)

    return deploy_to_device(
        repo_root=repo_root,
        serial=args.serial,
        build_so=not args.skip_build,
        push_so=push_so,
        build_payload=not args.skip_payload if args.payload_only else True,
        push_payload=push_payload,
        launch=args.launch,
    )


if __name__ == "__main__":
    sys.exit(main())
