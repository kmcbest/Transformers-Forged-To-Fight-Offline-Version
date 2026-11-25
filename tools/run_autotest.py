#!/usr/bin/env python3
"""
Host-side runner for the -DTFTF_AUTOTEST=1 APK on a connected Android device.
Zero-root: uses `adb forward tcp:8080 tcp:8080` to push test_scenario.json into
the app's private storage via inapk_server.c, then captures logcat + HTTP logs
until [AUTOTEST] SCENARIO_DONE or timeout.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PKG = "com.kabam.bigrobot"
ACTIVITY = f"{PKG}/com.explodingbarrel.Activity"

DEFAULT_SCENARIO = {
    "active": True,
    "name": "sideswipe_vs_movie_sideswipe",
    "qid": "1.1.1",
    "p0": {"bid": "sideswipe_cin_rotf"},
    "p1": {"bid": "sideswipe_gs"},
    "auto_fight": True,
    "freeze_enemy_ai": False,
    "dummy_invincible": False,
    "max_duration_ms": 25000,
}


def find_adb() -> str:
    for cand in [
        shutil.which("adb"),
        "D:/Android/Sdk/platform-tools/adb.exe",
        str(Path.home() / "Android/Sdk/platform-tools/adb.exe"),
    ]:
        if cand and Path(cand).exists():
            return str(cand)
    raise FileNotFoundError("adb.exe not found in PATH or standard SDK locations")


def adb_cmd(adb: str, serial: str | None, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [adb]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def http_post_json(url: str, payload: dict) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an automated skill test scenario on connected device")
    parser.add_argument("--scenario", type=Path, default=None, help="Path to scenario JSON file")
    parser.add_argument("--serial", type=str, default=None, help="ADB device serial")
    parser.add_argument("--port", type=int, default=8080, help="Local forwarded port for inapk_server")
    parser.add_argument("--timeout", type=int, default=90, help="Overall timeout in seconds")
    parser.add_argument("--out-log", type=Path, default=None, help="Optional file to save captured logs")
    args = parser.parse_args()

    scenario = DEFAULT_SCENARIO
    if args.scenario:
        scenario = json.loads(args.scenario.read_text(encoding="utf-8"))

    adb = find_adb()
    print(f"[*] Using adb: {adb}")
    adb_cmd(adb, args.serial, "forward", f"tcp:{args.port}", "tcp:8080")

    # Step 1: If a custom scenario JSON was passed, wake the app briefly to accept POST /__autotest/scenario
    if args.scenario:
        print(f"[*] Uploading scenario '{scenario.get('name', 'custom')}' via inapk_server...")
        adb_cmd(adb, args.serial, "shell", "am", "force-stop", PKG, check=False)
        adb_cmd(adb, args.serial, "shell", "am", "start", "-n", ACTIVITY)
        pushed = False
        for _ in range(30):
            try:
                res = http_post_json(f"http://127.0.0.1:{args.port}/__autotest/scenario", scenario)
                print(f"[*] Scenario upload reply: {res}")
                pushed = True
                break
            except Exception:
                time.sleep(0.5)
        if not pushed:
            print("[!] Could not reach inapk_server HTTP endpoint; falling back to external files dir push")
            tmp_json = Path("build/tmp_test_scenario.json")
            tmp_json.parent.mkdir(parents=True, exist_ok=True)
            tmp_json.write_text(json.dumps(scenario, ensure_ascii=False, indent=2), encoding="utf-8")
            adb_cmd(adb, args.serial, "push", str(tmp_json), f"/sdcard/Android/data/{PKG}/files/test_scenario.json", check=False)

    # Step 2: Fresh launch and stream logcat
    adb_cmd(adb, args.serial, "shell", "am", "force-stop", PKG, check=False)
    adb_cmd(adb, args.serial, "logcat", "-c", check=False)
    print(f"[*] Launching {ACTIVITY} ...")
    adb_cmd(adb, args.serial, "shell", "am", "start", "-n", ACTIVITY)

    # Re-ensure forward after relaunch
    adb_cmd(adb, args.serial, "forward", f"tcp:{args.port}", "tcp:8080", check=False)

    cmd = [adb]
    if args.serial:
        cmd.extend(["-s", args.serial])
    cmd.extend(["logcat", "-v", "time", "-s", "TFTFHOOK", "SKILL_DISP"])

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    captured: list[str] = []
    start_t = time.time()
    done = False
    faulted = False

    keywords = (
        "[AUTOTEST]",
        "SIDESWIPE_",
        "SKILL_",
        "APPLY_BUFF",
        "REMOVE_BUFF",
        "HIT_RESULT",
        "FAULT",
        "VIOLATION",
        "ROLL_CRIT",
        "EVADE",
        "SKILL_DISP",
    )

    try:
        while time.time() - start_t < args.timeout:
            if proc.stdout is None:
                break
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            line_s = line.rstrip("\r\n")
            captured.append(line_s)
            if any(k in line_s for k in keywords):
                print(line_s)
            if "[AUTOTEST] SCENARIO_DONE" in line_s:
                done = True
                break
            if "FAULT sig=" in line_s or "COMBAT_RULE_VIOLATION" in line_s:
                faulted = True
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

    if args.out_log:
        args.out_log.parent.mkdir(parents=True, exist_ok=True)
        args.out_log.write_text("\n".join(captured) + "\n", encoding="utf-8")
        print(f"[*] Saved full logcat to {args.out_log}")

    try:
        http_logs = http_get(f"http://127.0.0.1:{args.port}/__autotest/log")
        if http_logs:
            http_out = Path("build/autotest_last_ring.log")
            http_out.write_text(http_logs, encoding="utf-8")
            print(f"[*] Saved HTTP ring-buffer log to {http_out}")
    except Exception:
        pass

    if done and not faulted:
        print("\n[PASS] Scenario completed without faults.")
        return 0
    if faulted:
        print("\n[FAIL] Fault or combat rule violation detected!")
        return 2
    print("\n[TIMEOUT] Did not observe [AUTOTEST] SCENARIO_DONE within timeout.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
