#!/usr/bin/env python3
"""
Host-side runner for the -DTFTF_AUTOTEST=1 APK on a connected Android device.
Zero-root: uses `adb forward tcp:8080 tcp:8080` to push test_scenario.json into
the app's private storage via inapk_server.c, then captures logcat + HTTP logs
until [AUTOTEST] SCENARIO_DONE or timeout.
"""
import argparse
import json
import re
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
    repo_root = Path(__file__).resolve().parent.parent
    for cand in [
        str(repo_root / "toolchain/android-sdk/platform-tools/adb.exe"),
        shutil.which("adb"),
        "D:/Android/Sdk/platform-tools/adb.exe",
        str(Path.home() / "Android/Sdk/platform-tools/adb.exe"),
    ]:
        if cand and Path(cand).exists():
            return str(cand)
    raise FileNotFoundError("adb.exe not found in repo toolchain, PATH, or standard SDK locations")


def adb_cmd(adb: str, serial: str | None, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [adb]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def http_post_json(url: str, payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_only_indices(spec: str, total: int) -> list[int]:
    """Parse 1-based index selector like '2', '1,3', or '2-4' into 0-based sorted unique indices."""
    chosen: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo_s, hi_s = part.split("-", 1)
            lo, hi = int(lo_s), int(hi_s)
            for idx in range(lo, hi + 1):
                if 1 <= idx <= total:
                    chosen.add(idx - 1)
        else:
            idx = int(part)
            if 1 <= idx <= total:
                chosen.add(idx - 1)
    return sorted(chosen)


def is_inapk_alive(port: int) -> bool:
    try:
        res = http_get(f"http://127.0.0.1:{port}/__autotest/ping")
        return '"ok":true' in res
    except Exception:
        return False


def run_single_scenario(
    adb: str,
    serial: str | None,
    port: int,
    timeout: int,
    scenario: dict,
    upload_custom: bool,
    out_log: Path | None,
    reuse_running: bool = False,
) -> int:
    if serial and ":" in serial:
        adb_cmd(adb, None, "connect", serial, check=False)
    adb_cmd(adb, serial, "wait-for-device", check=False)
    adb_cmd(adb, serial, "forward", f"tcp:{port}", "tcp:8080")

    sc_name = scenario.get("name", "custom")
    alive = reuse_running and is_inapk_alive(port)

    if alive:
        adb_cmd(adb, serial, "logcat", "-c", check=False)
        print(f"[*] Hot-switching scenario '{sc_name}' via /__autotest/run (no app restart)...")
        res = http_post_json(f"http://127.0.0.1:{port}/__autotest/run", scenario)
        print(f"[*] Scenario queue reply: {res}")
    else:
        adb_cmd(adb, serial, "shell", "am", "force-stop", PKG, check=False)
        adb_cmd(adb, serial, "logcat", "-c", check=False)
        print(f"[*] Cold-launching {ACTIVITY} for '{sc_name}'...")
        adb_cmd(adb, serial, "shell", "am", "start", "-n", ACTIVITY)
        adb_cmd(adb, serial, "forward", f"tcp:{port}", "tcp:8080", check=False)
        if upload_custom:
            pushed = False
            for _ in range(40):
                try:
                    res = http_post_json(f"http://127.0.0.1:{port}/__autotest/run", scenario)
                    print(f"[*] Scenario queued during boot ({sc_name}): {res}")
                    pushed = True
                    break
                except Exception:
                    time.sleep(0.25)
            if not pushed:
                print("[!] Could not reach inapk_server HTTP endpoint; falling back to external files dir push")
                tmp_json = Path("build/tmp_test_scenario.json")
                tmp_json.parent.mkdir(parents=True, exist_ok=True)
                tmp_json.write_text(json.dumps(scenario, ensure_ascii=False, indent=2), encoding="utf-8")
                adb_cmd(adb, serial, "push", str(tmp_json), f"/sdcard/Android/data/{PKG}/files/test_scenario.json", check=False)
                adb_cmd(adb, serial, "shell", "am", "force-stop", PKG, check=False)
                adb_cmd(adb, serial, "shell", "am", "start", "-n", ACTIVITY)

    cmd = [adb]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(["logcat", "-v", "time", "-s", "TFTFHOOK", "SKILL_DISP"])

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    captured: list[str] = []
    start_t = time.time()
    done = False
    faulted = False
    started_run = False

    keywords = (
        "[AUTOTEST]",
        "[AB_TRACE]",
        "OVERLAY_HUD",
        "[OVERLAY]",
        "SIDESWIPE_",
        "ARCEE_",
        "ELITA_",
        "SPECIAL_LOCK",
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
        while time.time() - start_t < timeout:
            if proc.stdout is None:
                break
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
                continue
            line_s = line.rstrip("\r\n")
            if not started_run and f"[AUTOTEST] RUN_START name={sc_name}" in line_s:
                started_run = True
                captured.clear()
            captured.append(line_s)
            if any(k in line_s for k in keywords):
                print(line_s)
            if "[AUTOTEST] SCENARIO_DONE" in line_s and (f"name={sc_name}" in line_s or started_run):
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

    if out_log:
        out_log.parent.mkdir(parents=True, exist_ok=True)
        out_log.write_text("\n".join(captured) + "\n", encoding="utf-8")
        print(f"[*] Saved full logcat to {out_log}")

    try:
        http_logs = http_get(f"http://127.0.0.1:{port}/__autotest/log")
        if http_logs:
            http_out = Path("build/autotest_last_ring.log")
            http_out.write_text(http_logs, encoding="utf-8")
            print(f"[*] Saved HTTP ring-buffer log to {http_out}")
    except Exception:
        pass

    if faulted:
        print("\n[FAIL] Fault or combat rule violation detected!")
        return 2
    if not done:
        print("\n[TIMEOUT] Did not observe [AUTOTEST] SCENARIO_DONE within timeout.")
        return 1

    ok, errs = evaluate_assertions(scenario, captured)
    if ok:
        print("\n[PASS] Scenario completed and ALL AB_TRACE assertions passed.")
        return 0
    print("\n[FAIL] Scenario completed but AB_TRACE assertions failed:")
    for e in errs:
        print(f"  - {e}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an automated skill test scenario on connected device")
    parser.add_argument("--scenario", type=Path, default=None, help="Path to single scenario JSON file")
    parser.add_argument("--scenarios", nargs="+", type=Path, default=None, help="Ordered list of scenario JSON files")
    parser.add_argument("--only", type=str, default=None, help="1-based index selector for --scenarios (e.g. '2' or '1,3' or '2-4')")
    parser.add_argument("--deploy", action="store_true", help="Hot-deploy libdothook-autotest.so + payload to MuMu before running")
    parser.add_argument("--serial", type=str, default=None, help="ADB device serial")
    parser.add_argument("--port", type=int, default=8080, help="Local forwarded port for inapk_server")
    parser.add_argument("--timeout", type=int, default=90, help="Per-scenario timeout in seconds")
    parser.add_argument("--out-log", type=Path, default=None, help="Optional file to save captured logs")
    parser.add_argument("--dry-check-log", type=Path, default=None, help="Offline mode: evaluate assertions against a saved log file")
    args = parser.parse_args()

    if args.dry_check_log:
        scenario = json.loads(args.scenario.read_text(encoding="utf-8")) if args.scenario else DEFAULT_SCENARIO
        lines = args.dry_check_log.read_text(encoding="utf-8", errors="replace").splitlines()
        ok, errs = evaluate_assertions(scenario, lines)
        if ok:
            print("[PASS] Dry-check assertions succeeded.")
            return 0
        print("[FAIL] Dry-check assertions failed:")
        for e in errs:
            print(f"  - {e}")
        return 1

    if args.deploy:
        deploy_script = Path(__file__).resolve().parent / "deploy_autotest_mumu.py"
        dep_cmd = [sys.executable, str(deploy_script)]
        if args.serial:
            dep_cmd.extend(["--serial", args.serial])
        dep_res = subprocess.run(dep_cmd)
        if dep_res.returncode != 0:
            return dep_res.returncode

    adb = find_adb()
    print(f"[*] Using adb: {adb}")

    if args.scenarios:
        all_paths = args.scenarios
        indices = parse_only_indices(args.only, len(all_paths)) if args.only else list(range(len(all_paths)))
        if not indices:
            print(f"[!] --only '{args.only}' matched 0 of {len(all_paths)} scenarios.")
            return 1
        results: list[tuple[int, str, int]] = []
        suite_t0 = time.time()
        for pos, idx in enumerate(indices):
            sc_path = all_paths[idx]
            scenario = json.loads(sc_path.read_text(encoding="utf-8"))
            print(f"\n==================== [{idx + 1}/{len(all_paths)}] {scenario.get('name', sc_path.stem)} ({sc_path.name}) ====================")
            log_path = None
            if args.out_log:
                log_path = args.out_log.parent / f"{args.out_log.stem}_{idx + 1}_{sc_path.stem}{args.out_log.suffix or '.log'}"
            rc = run_single_scenario(adb, args.serial, args.port, args.timeout, scenario, True, log_path, reuse_running=(pos > 0))
            results.append((idx + 1, sc_path.name, rc))
        print(f"\n==================== AUTOTEST SUITE SUMMARY ({time.time() - suite_t0:.2f}s) ====================")
        overall_rc = 0
        for num, name, rc in results:
            status = "PASS" if rc == 0 else f"FAIL(rc={rc})"
            print(f"  #{num}: {name} -> {status}")
            if rc != 0:
                overall_rc = rc
        return overall_rc

    scenario = json.loads(args.scenario.read_text(encoding="utf-8")) if args.scenario else DEFAULT_SCENARIO
    return run_single_scenario(adb, args.serial, args.port, args.timeout, scenario, bool(args.scenario), args.out_log)


_AB_KV_RE = re.compile(r"(\w+)=([^\s]+)")


def _parse_ab_traces(lines: list[str]) -> list[dict[str, str]]:
    traces = []
    for ln in lines:
        idx = ln.find("[AB_TRACE]")
        if idx < 0:
            continue
        kv = dict(_AB_KV_RE.findall(ln[idx:]))
        if kv:
            traces.append(kv)
    return traces


def evaluate_assertions(scenario: dict, lines: list[str]) -> tuple[bool, list[str]]:
    assertions = scenario.get("assertions")
    if not assertions:
        return True, []

    traces = _parse_ab_traces(lines)
    errors: list[str] = []

    apply_events = [t for t in traces if t.get("EVT") == "APPLY_BUFF" and t.get("res", "0") != "0"]
    dot_events = [t for t in traces if t.get("EVT") == "DOT_TICK"]
    hit_events = [t for t in traces if t.get("EVT") == "HIT_CONNECTED"]
    roll_events = [t for t in traces if t.get("EVT") == "TEST_ROLL"]
    evade_events = [t for t in traces if t.get("EVT") == "EVADE" and t.get("res", "0") != "0"]

    for req in assertions.get("must_apply_buffs", []):
        tgt = req.get("target")
        substr = req.get("mod_substr", "")
        min_cnt = int(req.get("min_count", 1))
        max_cnt = req.get("max_count")
        matched = [
            e for e in apply_events
            if (not tgt or e.get("tgt") == tgt) and substr in e.get("mod", "")
        ]
        if len(matched) < min_cnt:
            errors.append(f"must_apply_buffs failed: tgt={tgt}, substr='{substr}', expected>={min_cnt}, got={len(matched)}")
        if max_cnt is not None and len(matched) > int(max_cnt):
            errors.append(f"must_apply_buffs failed: tgt={tgt}, substr='{substr}', expected<={int(max_cnt)}, got={len(matched)}")

    for forbid in assertions.get("must_not_apply_buffs", []):
        tgt = forbid.get("target")
        substr = forbid.get("mod_substr", "")
        matched = [
            e for e in apply_events
            if (not tgt or e.get("tgt") == tgt) and substr in e.get("mod", "")
        ]
        if matched:
            errors.append(f"must_not_apply_buffs failed: tgt={tgt}, substr='{substr}', got={len(matched)}")

    for dot_req in assertions.get("must_dot_tick", []):
        tgt = dot_req.get("target")
        min_ticks = int(dot_req.get("min_ticks", 1))
        min_dmg = float(dot_req.get("min_dmg", 1.0))
        matched = [
            e for e in dot_events
            if (not tgt or e.get("tgt") == tgt) and float(e.get("dmg", "0")) >= min_dmg
        ]
        if len(matched) < min_ticks:
            errors.append(f"must_dot_tick failed: tgt={tgt}, min_dmg={min_dmg}, expected_ticks>={min_ticks}, got={len(matched)}")

    for hit_req in assertions.get("must_hit_connected", []):
        att = hit_req.get("attacker")
        sp = hit_req.get("sp")
        min_cnt = int(hit_req.get("min_count", 1))
        matched = [
            e for e in hit_events
            if (not att or e.get("att") == att) and (sp is None or int(e.get("sp", "-1")) == int(sp))
        ]
        if len(matched) < min_cnt:
            errors.append(f"must_hit_connected failed: att={att}, sp={sp}, expected>={min_cnt}, got={len(matched)}")

    for roll_req in assertions.get("must_test_roll", []):
        substr = roll_req.get("mod_substr", "")
        min_cnt = int(roll_req.get("min_count", 1))
        matched = [e for e in roll_events if substr in e.get("mod", "")]
        if len(matched) < min_cnt:
            errors.append(f"must_test_roll failed: substr='{substr}', expected>={min_cnt}, got={len(matched)}")

    min_p1_dmg = assertions.get("min_p1_damage")
    if min_p1_dmg is not None:
        total_p1_dmg = sum(float(e.get("dmg", "0")) for e in hit_events if e.get("tgt") == "P1")
        total_p1_dmg += sum(float(e.get("dmg", "0")) for e in dot_events if e.get("tgt") == "P1")
        if total_p1_dmg < float(min_p1_dmg):
            errors.append(f"min_p1_damage failed: expected>={min_p1_dmg}, got={total_p1_dmg:.1f}")

    for ev_req in assertions.get("must_evade", []):
        tgt = ev_req.get("target")
        ranged = ev_req.get("ranged")
        min_cnt = int(ev_req.get("min_count", 1))
        matched = [
            e for e in evade_events
            if (not tgt or e.get("tgt") == tgt) and (ranged is None or int(e.get("ranged", "-1")) == int(ranged))
        ]
        if len(matched) < min_cnt:
            errors.append(f"must_evade failed: tgt={tgt}, ranged={ranged}, expected>={min_cnt}, got={len(matched)}")

    for cr_req in assertions.get("must_crit", []):
        att = cr_req.get("attacker")
        sp = cr_req.get("sp")
        min_cnt = int(cr_req.get("min_count", 1))
        matched = [
            e for e in hit_events
            if e.get("crit") == "1"
            and (not att or e.get("att") == att)
            and (sp is None or int(e.get("sp", "-1")) == int(sp))
        ]
        if len(matched) < min_cnt:
            errors.append(f"must_crit failed: att={att}, sp={sp}, expected>={min_cnt}, got={len(matched)}")

    for sub_req in assertions.get("must_log_substrings", []):
        substr = sub_req.get("substr", "")
        default_min = 0 if "max_count" in sub_req else 1
        min_cnt = int(sub_req.get("min_count", default_min))
        max_cnt = sub_req.get("max_count")
        matched = [ln for ln in lines if substr in ln]
        if len(matched) < min_cnt:
            errors.append(f"must_log_substrings failed: substr='{substr}', expected>={min_cnt}, got={len(matched)}")
        if max_cnt is not None and len(matched) > int(max_cnt):
            errors.append(f"must_log_substrings failed: substr='{substr}', expected<={int(max_cnt)}, got={len(matched)}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    sys.exit(main())
