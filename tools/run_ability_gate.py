#!/usr/bin/env python3
"""
TFTF 能力系统统一质量门禁运行器 (Unified Ability Quality Gate Runner)
==========================================================================
串联执行全部静态契约校验、快照防回归比对、hook.c 总线冻结检查、三端编译及模拟器单测，
并在指定 --device 时自动执行实机/模拟器金丝雀靶场验收 (Autotest Canaries)。

用法:
  python tools/run_ability_gate.py
  python tools/run_ability_gate.py --device
  python tools/run_ability_gate.py --device --serial emulator-5554
  python tools/run_ability_gate.py --skip-build
"""

import argparse
import glob
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOOK_C_PATH = os.path.join(REPO_ROOT, "tools", "nativehook", "hook.c")
CANARY_DIR = os.path.join(REPO_ROOT, "tools", "autotest_scenarios")


def run_step(title: str, cmd: list) -> bool:
    print(f"\n{'=' * 72}")
    print(f"▶ {title}")
    print(f"  $ {' '.join(cmd)}")
    print(f"{'=' * 72}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(cmd, cwd=REPO_ROOT, env=env)
    if res.returncode != 0:
        print(f"❌ [FAIL] {title} 失败 (exit code={res.returncode})")
        return False
    print(f"✅ [PASS] {title}")
    return True


def _extract_c_function(text: str, signature_prefix: str) -> str:
    idx = text.find(signature_prefix)
    if idx < 0:
        return ""
    brace_start = text.find("{", idx)
    if brace_start < 0:
        return ""
    depth = 0
    for pos in range(brace_start, len(text)):
        ch = text[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[idx : pos + 1]
    return ""


def check_hook_c_freeze() -> bool:
    print(f"\n{'=' * 72}")
    print("▶ 静态门禁: hook.c 事件总线冻结检查 (Freeze Check)")
    print(f"{'=' * 72}")

    if not os.path.isfile(HOOK_C_PATH):
        print(f"❌ 未找到 {HOOK_C_PATH}")
        return False

    with open(HOOK_C_PATH, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()

    # 1. 确认 hook_192 (TestRoll) 调用了 skill_dispatch_test_roll 且无任何角色名 strstr/strcmp 特判
    fn_192 = _extract_c_function(src, "int hook_192(")
    if not fn_192:
        print("❌ 未在 hook.c 中找到 int hook_192(")
        return False
    if "skill_dispatch_test_roll(" not in fn_192:
        print("❌ hook_192 未委托调用 skill_dispatch_test_roll")
        return False

    # 禁止在 hook_192 中出现任何针对 bot_id / owner_bot_id / bid / who 的 strstr/strcmp 特判
    bot_cmp_pat = re.compile(
        r"\b(strstr|strcmp|strncmp)\s*\(\s*(?:owner_bot_id|bot_id|bid|who|atk_bot|def_bot|g_p[01]_bot_id|mod_id)\b"
    )
    violations = []
    for line in fn_192.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        # hook_192 允许通过 modifier 通用前缀匹配做日志展示标签 (如 "armor_break", "burn" 等非角色名)
        if 'skill = "' in line:
            continue
        m = bot_cmp_pat.search(line)
        if m:
            violations.append(stripped)

    if violations:
        print("❌ hook_192 发现疑似角色硬编码判定（违反事件总线冻结铁律）：")
        for v in violations:
            print(f"   • {v}")
        return False

    # 2. 确认 hook_188 和 hook_177 保持向 skill_dispatcher 派发
    fn_188 = _extract_c_function(src, "int hook_188(")
    if "skill_dispatch_buff_applied(" not in fn_188:
        print("❌ hook_188 缺少 skill_dispatch_buff_applied 派发调用")
        return False

    fn_177 = _extract_c_function(src, "float hook_177(")
    if "skill_dispatch_hit_connected(" not in fn_177:
        print("❌ hook_177 缺少 skill_dispatch_hit_connected 派发调用")
        return False

    # 禁止在 hook_188 中引入针对具体角色名的 bot_id 硬编码判断
    for line in fn_188.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        if re.search(r"\b(strstr|strcmp)\s*\(\s*(?:owner_bot_id|bot_id|bid|who|g_p[01]_bot_id)\b", line):
            print(f"❌ hook_188 发现禁止的角色判定: {stripped}")
            return False

    print("✅ [PASS] hook.c 事件总线冻结校验通过 (hook_192/hook_188/hook_177 派发完整且无新增角色硬编码)")
    return True


def main():
    parser = argparse.ArgumentParser(description="TFTF 能力系统全链路质量门禁")
    parser.add_argument("--skip-build", action="store_true", help="跳过 C/NDK/Sim 编译步骤")
    parser.add_argument("--device", action="store_true", help="运行真机/模拟器金丝雀靶场验收 (canary_*.json)")
    parser.add_argument("--serial", default=None, help="ADB 设备序列号 (传给 run_autotest.py --serial)")
    parser.add_argument("--allow", default="", help="传给 snapshot_abilities.py --check 的白名单")
    args = parser.parse_args()

    py = sys.executable

    if not run_step("门禁 1/4: 严格契约与能力 Schema 校验 (--all --strict)", [py, "tools/validate_bot_ability.py", "--all", "--strict"]):
        sys.exit(1)

    snap_cmd = [py, "tools/snapshot_abilities.py", "--check"]
    if args.allow:
        snap_cmd.extend(["--allow", args.allow])
    if not run_step("门禁 2/4: 能力基准快照防回归校验 (--check)", snap_cmd):
        sys.exit(1)

    if not check_hook_c_freeze():
        sys.exit(1)

    if not args.skip_build:
        if not run_step("门禁 4A: 编译 NativeHook (tools/build_hook.py)", [py, "tools/build_hook.py"]):
            sys.exit(1)
        if not run_step("门禁 4B: 编译 Autotest 靶场库 (tools/build_hook.py --autotest)", [py, "tools/build_hook.py", "--autotest"]):
            sys.exit(1)
        if not run_step("门禁 4C: 编译数学/契约模拟器 DLL (tools/sim/build_sim.py)", [py, "tools/sim/build_sim.py"]):
            sys.exit(1)

    if not run_step("门禁 4D: 运行模拟器数学与契约测试 (tools/sim/run_tests.py)", [py, "tools/sim/run_tests.py"]):
        sys.exit(1)

    if args.device:
        canaries = sorted(glob.glob(os.path.join(CANARY_DIR, "canary_*.json")))
        if not canaries:
            print("❌ 未找到任何 tools/autotest_scenarios/canary_*.json 场景文件")
            sys.exit(1)
        for sc in canaries:
            rel = os.path.relpath(sc, REPO_ROOT)
            cmd = [py, "tools/run_autotest.py", "--scenario", rel]
            if args.serial:
                cmd.extend(["--serial", args.serial])
            if not run_step(f"实机/模拟器金丝雀验收: {os.path.basename(sc)}", cmd):
                sys.exit(1)
    else:
        print("\nℹ️  未指定 --device，已跳过实机/模拟器金丝雀验收 (MuMu 12 就绪后可加 --device 执行)。")

    print("\n" + "=" * 72)
    print("🎉 能力系统全链路质量门禁全部通过！(ALL GATES GREEN)")
    print("=" * 72)


if __name__ == "__main__":
    main()
