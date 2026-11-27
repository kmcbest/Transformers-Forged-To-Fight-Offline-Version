#!/usr/bin/env python3
"""
TFTF Accepted & Locked Bots Guard (已验收角色防篡改门禁)
========================================================
对已通过真机/靶场验收的代表人物进行加密哈希锁定，涵盖：
  1. Server/abilities/bots/<bot>.py
  2. tools/nativehook/skills/bots/skill_<bot>.c
  3. tools/autotest_scenarios/<bot>_*.json
  4. golden_abilities_snapshot.json 中对应 bot 的生成输出一致性

任何未授权修改（哪怕只改了一行注释或一个断言）都会触发 FAIL 阻断。
只有获得用户明确许可后，才能修改并使用 --lock <bot_id> 刷新锁哈希。

用法:
  python tools/check_accepted_lock.py --check
  python tools/check_accepted_lock.py --list
  python tools/check_accepted_lock.py --lock arcee_gs_deluxe2014
  python tools/check_accepted_lock.py --run-device --serial 127.0.0.1:7555
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "Server"
LOCK_PATH = SERVER_DIR / "abilities" / "accepted_bots_lock.json"
SNAPSHOT_PATH = SERVER_DIR / "abilities" / "golden_abilities_snapshot.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from abilities.registry import _BOT_REGISTRY, load_all_bots  # noqa: E402
from tools.snapshot_abilities import _canonicalize  # noqa: E402


_TEXT_EXTS = {".py", ".c", ".h", ".cpp", ".hpp", ".json", ".md", ".txt", ".sh", ".yml", ".yaml"}


def sha256_file(path: Path) -> str:
    """Compute file SHA-256, normalizing CRLF -> LF for text files so Git autocrlf cannot drift locks."""
    data = path.read_bytes()
    if path.suffix.lower() in _TEXT_EXTS or b"\x00" not in data:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def load_lock() -> Dict[str, Any]:
    if not LOCK_PATH.exists():
        return {"schema_version": 1, "bots": {}}
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def save_lock(data: Dict[str, Any]) -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_list(lock_data: Dict[str, Any]) -> int:
    bots = lock_data.get("bots", {})
    if not bots:
        print("ℹ️  当前尚无已验收锁定角色。")
        return 0
    print(f"🔒 已登记验收代表角色（共 {len(bots)} 位）:")
    for bid, info in bots.items():
        status = "LOCKED" if info.get("locked", False) else "UNLOCKED"
        name_zh = info.get("name_zh", "")
        arch = ", ".join(info.get("archetypes", []))
        sc_cnt = len(info.get("scenarios", []))
        file_cnt = len(info.get("files", {}))
        print(f"  - [{status}] {name_zh} ({bid}) | 类型: {arch} | 锁定文件: {file_cnt} | 剧本: {sc_cnt} | 验收日期: {info.get('accepted_at', '')}")
    return 0


def cmd_lock(lock_data: Dict[str, Any], bot_id: str, unlock: bool = False) -> int:
    bots = lock_data.get("bots", {})
    if bot_id not in bots:
        print(f"❌ 未在 {LOCK_PATH.relative_to(REPO_ROOT)} 中找到角色 '{bot_id}'，请先在该清单注册文件与剧本列表。")
        return 1
    entry = bots[bot_id]
    if unlock:
        entry["locked"] = False
        save_lock(lock_data)
        print(f"🔓 已解除锁定: {entry.get('name_zh', '')} ({bot_id})。修改并复验后请再次执行 --lock {bot_id}！")
        return 0

    files_map: Dict[str, str] = entry.get("files", {})
    if not files_map:
        print(f"❌ '{bot_id}' 未配置 files 列表。")
        return 1

    updated: Dict[str, str] = {}
    for rel_path in files_map.keys():
        abs_path = REPO_ROOT / rel_path
        if not abs_path.is_file():
            print(f"❌ 缺失被锁定文件: {rel_path}")
            return 1
        updated[rel_path] = sha256_file(abs_path)

    entry["files"] = updated
    entry["locked"] = True
    entry["locked_at"] = date.today().isoformat()
    save_lock(lock_data)
    print(f"🔒 已更新并锁定 {entry.get('name_zh', '')} ({bot_id})，共锁定 {len(updated)} 个文件 SHA-256。")
    return 0


def _check_snapshot_for_bot(bot_id: str, golden_bots: Dict[str, Any]) -> str:
    if bot_id not in _BOT_REGISTRY:
        return f"当前库中缺失已锁定角色 {bot_id}"
    reg = _BOT_REGISTRY[bot_id]
    res = reg["builder"](base_hp=34850.0, base_atk=3485.0)
    if isinstance(res, (tuple, list)) and len(res) == 2:
        mods, appears = res
        buffs = {}
    else:
        mods, appears, buffs = res[0], res[1], res[2]
    cur_entry = {
        "name_zh": reg.get("name_zh", ""),
        "mods": _canonicalize(mods),
        "appears": _canonicalize(appears),
        "buffs": _canonicalize(buffs),
    }
    if bot_id not in golden_bots:
        return f"golden_abilities_snapshot.json 中缺失 {bot_id}"
    if golden_bots[bot_id] != cur_entry:
        return f"能力生成结果与 golden_abilities_snapshot.json 不一致（可能受到 core/公共配置连带影响）"
    return ""


def cmd_check(lock_data: Dict[str, Any]) -> int:
    bots = lock_data.get("bots", {})
    locked_items = [(bid, info) for bid, info in bots.items() if info.get("locked", False)]
    if not locked_items:
        print("ℹ️  当前无 locked=true 的已验收角色，跳过防篡改检查。")
        return 0

    golden_bots: Dict[str, Any] = {}
    if SNAPSHOT_PATH.is_file():
        golden_bots = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")).get("bots", {})
    load_all_bots()

    violations: List[str] = []
    for bid, info in locked_items:
        name_zh = info.get("name_zh", bid)
        files_map: Dict[str, str] = info.get("files", {})
        for rel_path, expected_hash in files_map.items():
            abs_path = REPO_ROOT / rel_path
            if not abs_path.is_file():
                violations.append(f"[{name_zh} ({bid})] 被锁定文件丢失: {rel_path}")
                continue
            actual_hash = sha256_file(abs_path)
            if not expected_hash or actual_hash != expected_hash:
                violations.append(
                    f"[{name_zh} ({bid})] 被锁定文件遭篡改或未刷新锁: {rel_path} "
                    f"(expected={str(expected_hash)[:12]}..., actual={actual_hash[:12]}...)"
                )
        snap_err = _check_snapshot_for_bot(bid, golden_bots)
        if snap_err:
            violations.append(f"[{name_zh} ({bid})] {snap_err}")

    if violations:
        print("\n❌ [LOCKED BOT VIOLATION] 检测到已验收锁定角色发生未授权改动:")
        for v in violations:
            print(f"   • {v}")
        print("\n🚫 已验收代表角色受保护！严禁擅自修改已锁定角色的 Python/C/靶场剧本。")
        print("   若确因用户明确要求修复而变更，请在重验通过并获用户确认后执行:")
        print("   python tools/check_accepted_lock.py --lock <bot_id>")
        return 1

    print(f"🔒 已验收锁定角色校验通过！共校验 {len(locked_items)} 位锁定角色的全部源码、剧本及快照哈希一致。")
    return 0


def cmd_run_device(lock_data: Dict[str, Any], bot_id: str | None, serial: str | None) -> int:
    bots = lock_data.get("bots", {})
    scenarios: List[str] = []
    for bid, info in bots.items():
        if bot_id and bid != bot_id:
            continue
        if not info.get("locked", False):
            continue
        scenarios.extend(info.get("scenarios", []))
    if not scenarios:
        print("❌ 未找到匹配的可执行锁定剧本。")
        return 1
    cmd = [sys.executable, "tools/run_autotest.py", "--deploy"]
    if serial:
        cmd.extend(["--serial", serial])
    cmd.append("--scenarios")
    cmd.extend(scenarios)
    print(f"▶ 执行已验收角色回归剧本 ({len(scenarios)} 个场景): {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=REPO_ROOT)
    return res.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="TFTF Accepted & Locked Bots Guard")
    parser.add_argument("--check", action="store_true", help="校验所有已锁定角色的源码/剧本/快照哈希")
    parser.add_argument("--list", action="store_true", help="列出所有已登记的验收代表角色")
    parser.add_argument("--lock", type=str, default=None, help="计算并锁定指定 bot_id 的文件哈希")
    parser.add_argument("--unlock", type=str, default=None, help="临时解锁指定 bot_id（需配合后续重验与 --lock）")
    parser.add_argument("--run-device", action="store_true", help="一键在设备/模拟器重跑已锁定角色回归剧本")
    parser.add_argument("--bot", type=str, default=None, help="配合 --run-device 指定单个 bot_id")
    parser.add_argument("--serial", type=str, default=None, help="ADB 设备序列号")
    args = parser.parse_args()

    lock_data = load_lock()

    if args.list:
        return cmd_list(lock_data)
    if args.lock:
        return cmd_lock(lock_data, args.lock, unlock=False)
    if args.unlock:
        return cmd_lock(lock_data, args.unlock, unlock=True)
    if args.run_device:
        return cmd_run_device(lock_data, args.bot, args.serial)
    return cmd_check(lock_data)


if __name__ == "__main__":
    sys.exit(main())
