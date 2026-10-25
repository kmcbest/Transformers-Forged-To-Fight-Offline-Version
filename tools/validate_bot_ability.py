#!/usr/bin/env python3
"""
TFTF Bot Ability Quality Gate & Contract Validator
=================================================
自动化验证特定机器人的技能实现模块 (Server/abilities/bots/<bot_id>.py) 是否符合：
  1. 真理源对照：检查官方数据库 (character_abilities) 中的中文技能描述；
  2. 底层契约：校验 tr/uit/a 列表包装、颜色纯 6 位 Hex、数值截断防护；
  3. 数据完整性：确保 StatMod、StatModAppear 与 Buffs 交叉引用一致。

用法:
  python tools/validate_bot_ability.py arcee_gs_deluxe2014
  python tools/validate_bot_ability.py --all
"""

import sys
import os
import sqlite3
import argparse
import importlib
from pathlib import Path

# 确保在 Windows 控制台下正常输出 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 添加 Server 目录到 Python 搜索路径
REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "Server"
DB_PATH = SERVER_DIR / "tftf_database.db"

if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

import abilities
from abilities.core import validate_color_code, validate_statmod, validate_appear
from abilities.registry import _BOT_REGISTRY, load_all_bots


def query_ground_truth(bot_id: str):
    """从真理源获取该角色的官方中英文技能列表（优先本地数据库，缺损时回退至在线静态 CDN API）。"""
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT category, title_zh, title_en, desc_zh, desc_en, pua_icon, sort_order
                FROM character_abilities
                WHERE bot_id = ?
                ORDER BY sort_order ASC
                """,
                (bot_id,),
            )
            rows = cursor.fetchall()
            conn.close()
            if rows:
                return rows, "本地 SQLite 数据库 (Server/tftf_database.db)"
        except Exception as e:
            print(f"[WARN] 查询本地真理源数据库失败: {e}")

    # 回退到在线静态 CDN API
    try:
        import json
        import urllib.request
        url = f"https://kmcbest.github.io/tftfr/data/characters/{bot_id}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "TFTF-Validator/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            abilities = data.get("abilities", [])
            rows = []
            for idx, a in enumerate(abilities):
                rows.append((
                    a.get("category", ""),
                    a.get("title_zh", ""),
                    a.get("title_en", ""),
                    a.get("desc_zh", ""),
                    a.get("desc_en", ""),
                    a.get("pua_icon", ""),
                    idx + 1
                ))
            if rows:
                return rows, f"在线 CDN API ({url})"
    except Exception as e:
        pass

    return [], "None"


def validate_single_bot(bot_id: str, verbose: bool = True) -> bool:
    """验证单个机器人的能力实现，返回 True 表示全部通过，False 表示存在严重契约违规。"""
    print("=" * 80)
    print(f"🤖 开始校验机器人能力模块: [{bot_id}]")
    print("=" * 80)

    # 1. 查找真理源
    gt_rows, source_name = query_ground_truth(bot_id)
    if gt_rows:
        print(f"📖 【官方技能真理源】来源: {source_name} (共收录 {len(gt_rows)} 个官方技能):")
        for cat, t_zh, t_en, d_zh, d_en, pua, order in gt_rows:
            pua_str = f" [图标: {pua}]" if pua else ""
            print(f"   • [{cat}] {t_zh} ({t_en}){pua_str}")
            print(f"     官方描述: {d_zh}")
    else:
        print(f"⚠️  未在真理源（本地数据库与在线 CDN）中检索到 [{bot_id}] 的官方描述。")

    print("-" * 80)

    # 2. 检查模块与注册
    load_all_bots()
    if bot_id not in _BOT_REGISTRY:
        print(f"❌ [FAIL] 机器人 [{bot_id}] 未在 Server/abilities/registry.py 注册！")
        print("   请确保在 Server/abilities/bots/ 下创建对应 py 文件并添加 @register_bot 装饰器。")
        return False

    reg = _BOT_REGISTRY[bot_id]
    builder = reg["builder"]
    bot_name = reg.get("name_zh", "")
    bot_desc = reg.get("desc", "")
    print(f"✅ 注册信息检查通过: {bot_name} - {bot_desc}")

    # 3. 执行能力生成测试
    test_hp = 34850.0
    test_atk = 3485.0
    try:
        res = builder(base_hp=test_hp, base_atk=test_atk)
    except Exception as e:
        print(f"❌ [FAIL] 调用 builder(base_hp, base_atk) 抛出异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    if isinstance(res, (tuple, list)) and len(res) == 2:
        mods, appears = res
        buffs = {}
    elif isinstance(res, (tuple, list)) and len(res) >= 3:
        mods, appears, buffs = res[0], res[1], res[2]
    else:
        print(f"❌ [FAIL] builder 必须返回 (mods, appears) 或 (mods, appears, buffs)，得到类型: {type(res)}")
        return False

    print(f"📦 生成产物统计: {len(mods)} 个 StatMods, {len(appears)} 个 Appears, {len(buffs)} 个 Buffs")

    # 4. 严格契约审查
    errors = []
    warnings = []

    # 4.1 审查 StatMods
    for mod_id, mod in mods.items():
        try:
            validate_statmod(mod)
        except Exception as e:
            errors.append(f"StatMod [{mod_id}] 契约校验失败: {e}")

        # 检查列表类型 (tr, uit, a, au)
        for field in ("tr", "uit", "a", "au"):
            if not isinstance(mod.get(field), list):
                errors.append(f"StatMod [{mod_id}] 字段 '{field}' 必须为 List！得到: {type(mod.get(field))}")

        # 检查目标演员
        if mod.get("ta") not in ("self", "opponent"):
            warnings.append(f"StatMod [{mod_id}] 目标 'ta' 为 '{mod.get('ta')}'，建议为 'self' 或 'opponent'")

        # 检查伤害 Tick 截断 (仅针对造成持续伤害的 dmg_* 类修饰器)
        t = str(mod.get("t", ""))
        d = float(mod.get("d", 0.0))
        m = float(mod.get("m", 0.0))
        if t.startswith("dmg_") and d > 0 and m > 0:
            per_tick = m / (d * 2.0)
            if per_tick < 1.0:
                errors.append(
                    f"StatMod [{mod_id}] Tick 伤害截断风险: m={m} 在 d={d}s 下每跳为 {per_tick:.2f} < 1.0，客户端整数强转会导致 0 伤害！"
                )

        # 检查外观关联引用
        for appr_ref in mod.get("a", []):
            if appr_ref not in appears and not appr_ref.startswith("appr_sp_"):
                warnings.append(f"StatMod [{mod_id}] 关联的外观 '{appr_ref}' 未在 appears 中定义！")

    # 4.2 审查 StatModAppears
    for appr_id, appr in appears.items():
        try:
            validate_appear(appr)
        except Exception as e:
            errors.append(f"Appear [{appr_id}] 校验失败: {e}")

        for color_field in ("tc", "gt", "gb", "bc"):
            c_val = appr.get(color_field)
            if c_val:
                try:
                    validate_color_code(c_val, f"{appr_id}.{color_field}")
                except Exception as e:
                    errors.append(f"Appear [{appr_id}] 颜色不合规: {e}")

    # 4.3 审查 Buffs
    for buff_id, buff in buffs.items():
        if "id" not in buff or "buffType" not in buff:
            errors.append(f"Buff [{buff_id}] 缺少必需字段 'id' 或 'buffType'")

    # 5. 汇报审查结果
    if warnings:
        print("\n⚠️  【契约警告 (Warnings)】:")
        for w in warnings:
            print(f"   [WARN] {w}")

    if errors:
        print("\n❌ 【契约严重违规 (Errors)】:")
        for err in errors:
            print(f"   [FAIL] {err}")
        print(f"\n🚫 校验未通过！共发现 {len(errors)} 个严重错误，{len(warnings)} 个警告。")
        return False
    else:
        print(f"\n✨ 恭喜！机器人 [{bot_id}] 能力模块通过全部底层契约与数据完整性校验！")
        return True


def main():
    parser = argparse.ArgumentParser(description="TFTF Bot Ability Quality Gate")
    parser.add_argument("bot_id", nargs="?", default="", help="机器人唯一 ID (如 arcee_gs_deluxe2014)")
    parser.add_argument("--all", action="store_true", help="校验所有已注册的机器人模块")
    args = parser.parse_args()

    if args.all:
        load_all_bots()
        bots = list(_BOT_REGISTRY.keys())
        if not bots:
            print("未在 Server/abilities/bots/ 目录下发现任何注册的机器人模块。")
            sys.exit(1)
        all_passed = True
        for b in bots:
            ok = validate_single_bot(b)
            if not ok:
                all_passed = False
        sys.exit(0 if all_passed else 1)

    if not args.bot_id:
        # 默认测试 arcee
        target = "arcee_gs_deluxe2014"
        print(f"未指定 bot_id，默认校验标杆角色: [{target}]")
        ok = validate_single_bot(target)
        sys.exit(0 if ok else 1)
    else:
        ok = validate_single_bot(args.bot_id)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
