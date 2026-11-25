#!/usr/bin/env python3
"""
TFTF Abilities Golden Snapshot & Anti-Regression Gate
=====================================================
导出或比对 Server/abilities/ 生成的标准化全角色能力快照。
用于确保新增或修改单个角色能力时，未授权的其他老角色数据不发生任何隐性回归。

用法:
  python tools/snapshot_abilities.py --export
  python tools/snapshot_abilities.py --check
  python tools/snapshot_abilities.py --check --allow rhinox_gs_voyager2014 optimusprime_cin_tf
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "Server"
SNAPSHOT_PATH = SERVER_DIR / "abilities" / "golden_abilities_snapshot.json"

if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from abilities.registry import _BOT_REGISTRY, load_all_bots


def _canonicalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _canonicalize(obj[k]) for k in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_canonicalize(x) for x in obj]
    if isinstance(obj, float):
        return round(obj, 6)
    return obj


def build_snapshot() -> Dict[str, Any]:
    load_all_bots()
    bots_data: Dict[str, Any] = {}
    for bot_id in sorted(_BOT_REGISTRY.keys()):
        reg = _BOT_REGISTRY[bot_id]
        builder = reg["builder"]
        res = builder(base_hp=34850.0, base_atk=3485.0)
        if isinstance(res, (tuple, list)) and len(res) == 2:
            mods, appears = res
            buffs = {}
        elif isinstance(res, (tuple, list)) and len(res) >= 3:
            mods, appears, buffs = res[0], res[1], res[2]
        else:
            raise ValueError(f"Bot [{bot_id}] builder 返回格式非法: {type(res)}")

        bots_data[bot_id] = {
            "name_zh": reg.get("name_zh", ""),
            "mods": _canonicalize(mods),
            "appears": _canonicalize(appears),
            "buffs": _canonicalize(buffs),
        }

    return {
        "schema_version": 1,
        "base_hp": 34850.0,
        "base_atk": 3485.0,
        "bot_count": len(bots_data),
        "bots": bots_data,
    }


def _summarize_bot_diff(old_entry: Dict[str, Any], new_entry: Dict[str, Any]) -> List[str]:
    diffs: List[str] = []
    for section in ("mods", "appears", "buffs"):
        old_sec = old_entry.get(section, {})
        new_sec = new_entry.get(section, {})
        old_keys = set(old_sec.keys())
        new_keys = set(new_sec.keys())
        for added in sorted(new_keys - old_keys):
            diffs.append(f"+ {section}.{added}")
        for removed in sorted(old_keys - new_keys):
            diffs.append(f"- {section}.{removed}")
        for common in sorted(old_keys & new_keys):
            if old_sec[common] != new_sec[common]:
                diffs.append(f"~ {section}.{common}")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description="TFTF Abilities Golden Snapshot Tool")
    parser.add_argument("--export", action="store_true", help="导出当前全库能力为基准快照")
    parser.add_argument("--check", action="store_true", help="比对当前能力输出与基准快照差异")
    parser.add_argument("--allow", nargs="*", default=[], help="本次允许变更的 bot_id 列表")
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT_PATH, help="快照文件路径")
    args = parser.parse_args()

    if not args.export and not args.check:
        args.check = True

    current = build_snapshot()

    if args.export:
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] 已导出 {current['bot_count']} 个角色能力基准快照至: {args.snapshot}")
        return 0

    if not args.snapshot.exists():
        print(f"[FAIL] 未找到基准快照文件: {args.snapshot}，请先执行 --export")
        return 1

    golden = json.loads(args.snapshot.read_text(encoding="utf-8"))
    old_bots = golden.get("bots", {})
    new_bots = current.get("bots", {})
    allow_set = set(args.allow)

    all_ids = sorted(set(old_bots.keys()) | set(new_bots.keys()))
    unexpected_changes: List[str] = []
    allowed_changes: List[str] = []

    for bid in all_ids:
        if bid not in old_bots:
            line = f"[NEW BOT] {bid} (不在基准快照中)"
            (allowed_changes if bid in allow_set else unexpected_changes).append(line)
        elif bid not in new_bots:
            line = f"[REMOVED BOT] {bid} (从当前库中消失)"
            (allowed_changes if bid in allow_set else unexpected_changes).append(line)
        elif old_bots[bid] != new_bots[bid]:
            detail = ", ".join(_summarize_bot_diff(old_bots[bid], new_bots[bid])[:8])
            line = f"[MODIFIED] {bid}: {detail}"
            (allowed_changes if bid in allow_set else unexpected_changes).append(line)

    if allowed_changes:
        print("ℹ️  【已授权变更 (Allowed via --allow)】:")
        for item in allowed_changes:
            print(f"   {item}")

    if unexpected_changes:
        print("\n❌ 【未授权的老角色能力回归/漂移 (Unexpected Snapshot Drift)】:")
        for item in unexpected_changes:
            print(f"   {item}")
        print(f"\n🚫 快照防回归校验失败：发现 {len(unexpected_changes)} 个未在 --allow 白名单内的角色发生变化！")
        return 1

    print(f"✅ 快照防回归校验通过！共比对 {len(all_ids)} 个角色，未发生任何未授权能力漂移。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
