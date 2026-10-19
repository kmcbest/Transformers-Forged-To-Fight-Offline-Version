#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator for all remaining bots in Server/abilities/bots/
=========================================================
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOTS_DIR = REPO_ROOT / "Server" / "abilities" / "bots"
BOTS_DIR.mkdir(parents=True, exist_ok=True)

BOT_TEMPLATES = {}

# ---------------------------------------------------------------------------
# 2. 钢锁 (grimlock.py) - 7 项
# ---------------------------------------------------------------------------
BOT_TEMPLATES["grimlock.py"] = '''#!/usr/bin/env python3
"""
Bot Ability Implementation: 钢锁 (Grimlock)
===========================================
Bot ID: grimlock_gs_mp08
阵营: 汽车人 (Autobot) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战增益] (ID: 2532, pua_icon: 0xe406)
   - 受到攻击时 14% 概率得到一层近战增益 (+14% 近战伤害，持续 5s，可叠加)。
2. [觉醒 - 恐龙之怒] (ID: 2534, pua_icon: 无)
   - 受到伤害减益后 1 秒净化该减益，并有 30% 概率得到一层近战增益 (+30% 近战伤害，持续 5s，可叠加)。
3. [被动 - 燃烧] (ID: 2542, pua_icon: 0xe41d)
   - 重击命中时有 70% 几率造成燃烧，施加攻击力 50% 的伤害，持续 2 秒。
4. [被动 - 不可阻挡] (ID: 2543, pua_icon: 0xe915)
   - 重击全程进入不可阻挡状态。
5. [SP1 - 近战增益] (ID: 2544, pua_icon: 0xe406)
   - 100% 概率得到一层近战增益，增加近战伤害 12%，持续 5 秒。
6. [SP1 - 燃烧] (ID: 2545, pua_icon: 0xe41d)
   - 100% 几率造成燃烧，施加攻击力 100% 的伤害，持续 4 秒。
7. [SP2 - 近战增益] (ID: 2546, pua_icon: 0xe406)
   - 100% 概率得到一层近战增益，增加近战伤害 18%，持续 5 秒。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_burn_statmod,
    make_unstoppable_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "grimlock_gs_mp08"


@register_bot(BOT_ID, name_zh="钢锁", desc="格斗系暴龙领袖，受创累加近战增益，恐龙之怒净化DOT减益，重击霸体与暴烈喷火燃烧")
def build_grimlock_abilities(base_hp: float = 34000.0, base_atk: float = 2100.0):
    mods = {}
    appears = {}

    # 1. 被动近战增益 (ID: 2532): 受击 14% 几率获得 14% 近战增益 (5s, 可叠加)
    m_hit, a_hit = make_attack_boost_statmod(
        mod_id="grimlock_takehit_melee_buff",
        duration=5.0,
        attack_bonus=0.14,
        chance=0.14,
        trigger="onPreDamage",
        trigger_scope="",
        appr_id="appr_grimlock_takehit_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\\uE406",
        color_hex="F59E0B",
        gradient_bottom="D97706",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_hit)
    appears.update(a_hit)

    # 2. 觉醒恐龙之怒 (ID: 2534): 受到伤害减益后 1 秒净化该减益，并 30% 概率获 30% 近战增益 (5s)
    validate_color_code("EF4444", "dino_rage_tc")
    validate_color_code("B91C1C", "dino_rage_gb")
    appr_rage = {
        "id": "appr_grimlock_dino_rage",
        "a": "恐龙之怒",
        "s": "恐龙之怒",
        "l": "受到伤害减益1秒后净化，并有30%概率获得近战增益",
        "ss": "伤害减益延时净化",
        "t": "\\uE406",
        "f": "",
        "st": "恐龙之怒",
        "ps": "恐龙之怒",
        "pl": "恐龙之怒生效中",
        "tc": "EF4444",
        "gt": "EF4444",
        "gb": "B91C1C",
    }
    mod_rage = {
        "id": "grimlock_dino_rage",
        "t": "passive",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.30,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "dino_rage",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_grimlock_dino_rage"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_rage)
    mods["grimlock_dino_rage"] = mod_rage
    appears["appr_grimlock_dino_rage"] = appr_rage

    # 3. 重击燃烧 (ID: 2542): 70% 几率施加 2 秒 50% ATK 燃烧
    m_hb, a_hb = make_burn_statmod(
        mod_id="grimlock_heavy_burn",
        duration=2.0,
        total_dmg=float(round(base_atk * 0.50)),
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_grimlock_heavy_burn",
        callout_text="燃烧",
        show_callout=True,
        pua_icon="\\uE41D",
    )
    mods.update(m_hb)
    appears.update(a_hb)

    # 4. 重击不可阻挡 (ID: 2543): 重击全程霸体
    m_unstop, a_unstop = make_unstoppable_statmod(
        mod_id="grimlock_heavy_unstoppable",
        duration=3.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=HeavyCharge",
        appr_id="appr_grimlock_heavy_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        pua_icon="\\uE915",
    )
    mods.update(m_unstop)
    appears.update(a_unstop)

    # 5. SP1 近战增益 (ID: 2544): 100% 获 12% 近战增益 5s
    m_sp1_atk, a_sp1_atk = make_attack_boost_statmod(
        mod_id="grimlock_sp1_melee_buff",
        duration=5.0,
        attack_bonus=0.12,
        chance=1.0,
        trigger="onSpecial1Activate",
        appr_id="appr_grimlock_sp1_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\\uE406",
    )
    mods.update(m_sp1_atk)
    appears.update(a_sp1_atk)

    # 6. SP1 燃烧 (ID: 2545): 100% 施加 4 秒 100% ATK 燃烧
    m_sp1_b, a_sp1_b = make_burn_statmod(
        mod_id="grimlock_sp1_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_grimlock_sp1_burn",
        callout_text="燃烧",
        show_callout=True,
        pua_icon="\\uE41D",
    )
    mods.update(m_sp1_b)
    appears.update(a_sp1_b)

    # 7. SP2 近战增益 (ID: 2546): 100% 获 18% 近战增益 5s
    m_sp2_atk, a_sp2_atk = make_attack_boost_statmod(
        mod_id="grimlock_sp2_melee_buff",
        duration=5.0,
        attack_bonus=0.18,
        chance=1.0,
        trigger="onSpecial2Activate",
        appr_id="appr_grimlock_sp2_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\\uE406",
    )
    mods.update(m_sp2_atk)
    appears.update(a_sp2_atk)

    return mods, appears
'''

# ---------------------------------------------------------------------------
# 3. 野牛 (tantrum.py) - 5 项
# ---------------------------------------------------------------------------
BOT_TEMPLATES["tantrum.py"] = '''#!/usr/bin/env python3
"""
Bot Ability Implementation: 野牛 (Tantrum)
=========================================
Bot ID: tantrum_gs_kabam
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 不可阻挡] (ID: 3438, pua_icon: 0xe915)
   - 进入防御状态 1.5 秒后，获得 4.5 秒不可阻挡增益 (灰色倒计时 1.5s 后变黄色不可阻挡)。
2. [被动 - 近战增益] (ID: 3450, pua_icon: 0xe412)
   - 前冲时 100% 获得一层近战增益，增加 24% 近战伤害，最大叠加 10 层 (无倒计时)。
     如果野牛后闪且身上没有不可阻挡状态，则失去所有近战增益。
3. [被动 - 天然护甲] (ID: 3451, pua_icon: 无)
   - +10% 永久护甲增益，无图标，不可被破甲移除。
4. [SP3 - 不可阻挡] (ID: 3453, pua_icon: 0xe915)
   - 技能结束后获得 7.5 秒不可阻挡增益。
5. [SP3 - 近战增益] (ID: 3454, pua_icon: 0xe412)
   - 技能结束后获得 3 层近战增益，每层增加 24% 近战伤害，最大叠加 10 层。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_armor_up_statmod,
    make_unstoppable_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "tantrum_gs_kabam"


@register_bot(BOT_ID, name_zh="野牛", desc="格斗系狂暴冲锋者，防御蓄力爆发霸体，前冲叠加巨额近战伤害，天然重甲")
def build_tantrum_abilities(base_hp: float = 36000.0, base_atk: float = 2150.0):
    mods = {}
    appears = {}

    # 1a. 防御蓄力 (ID: 3438a): 防御进入时触发灰色倒计时图标 1.5 秒
    m_charge, a_charge = make_attack_boost_statmod(
        mod_id="tantrum_block_charge",
        duration=1.5,
        attack_bonus=0.0,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_tantrum_block_charge",
        callout_text="",
        show_callout=False,
        pua_icon="\\uE915",
        color_hex="CBD5E1",
        gradient_bottom="64748B",
        stackable=False,
    )
    mods.update(m_charge)
    appears.update(a_charge)

    # 1b. 防御不可阻挡 (ID: 3438b): 防御持续 1.5s 后由 NativeHook 主动施加 4.5s 霸体
    m_unstop, a_unstop = make_unstoppable_statmod(
        mod_id="tantrum_block_unstoppable",
        duration=4.5,
        trigger="manual",
        trigger_scope="",
        appr_id="appr_tantrum_block_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        pua_icon="\\uE915",
        color_hex="FFAA00",
    )
    mods.update(m_unstop)
    appears.update(a_unstop)

    # 2. 前冲近战增益 (ID: 3450): 前冲 100% 获得 24% 近战增益 (最多 10 层，后闪且无霸体清除)
    m_dash, a_dash = make_attack_boost_statmod(
        mod_id="tantrum_dash_melee_buff",
        duration=0.0,
        attack_bonus=0.24,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Dash",
        appr_id="appr_tantrum_dash_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\\uE412",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_dash)
    appears.update(a_dash)

    # 3. 天然护甲 (ID: 3451): +10% 永久护甲，不可破甲移除
    m_arm, a_arm = make_armor_up_statmod(
        mod_id="tantrum_innate_armor",
        duration=0.0,
        armor_bonus=0.10,
        chance=1.0,
        trigger="always",
        trigger_scope="",
        appr_id="appr_tantrum_innate_armor",
        callout_text="护甲",
        show_callout=False,
        stackable=False,
    )
    mods.update(m_arm)
    appears.update(a_arm)

    # 4. SP3 不可阻挡 (ID: 3453): 技能结束获得 7.5s 不可阻挡
    m_sp3_u, a_sp3_u = make_unstoppable_statmod(
        mod_id="tantrum_sp3_unstoppable",
        duration=7.5,
        trigger="onSpecial3Expiry",
        trigger_scope="",
        appr_id="appr_tantrum_sp3_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        pua_icon="\\uE915",
    )
    mods.update(m_sp3_u)
    appears.update(a_sp3_u)

    # 5. SP3 近战增益 (ID: 3454): 技能结束获得 3 层近战增益 (+72% 伤害)
    m_sp3_atk, a_sp3_atk = make_attack_boost_statmod(
        mod_id="tantrum_sp3_melee_buff",
        duration=0.0,
        attack_bonus=0.72,
        chance=1.0,
        trigger="onSpecial3Expiry",
        trigger_scope="",
        appr_id="appr_tantrum_sp3_melee_buff",
        callout_text="近战增益",
        show_callout=True,
        pua_icon="\\uE412",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sp3_atk)
    appears.update(a_sp3_atk)

    return mods, appears
'''

for fn, code in BOT_TEMPLATES.items():
    (BOTS_DIR / fn).write_text(code, encoding="utf-8")
    print(f"Wrote Server/abilities/bots/{fn}")
