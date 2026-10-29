#!/usr/bin/env python3
"""
Bot Ability Implementation: 搅拌者 (Mixmaster ROTF)
===================================================
Bot ID: mixmaster_cin_rotf
阵营: 霸天虎 (Decepticon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP2 - 强酸/腐蚀燃烧 / Acid Burn] (ID: 3178, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "60%概率造成燃烧，施加攻击力100%的伤害，持续8秒。"

2. [SP3 - 熔炉烈焰 / Caustic Blast Burn] (ID: 3179, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "70%概率造成燃烧，施加攻击力120%的伤害，持续8秒。"

3. [被动 - 远程酸液 / Ranged Acid] (ID: 3180, pua_icon: 0xe41d, category: passive)
   - 官方描述: "远程攻击第1击和第2击：30%的概率施加1层酸液减益，造成攻击力45%的伤害，持续9秒。"

4. [特殊技 3 - 强酸融化 / SP3 Acid] (ID: 3181, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "施加1层酸液减益，造成攻击力134%的伤害，持续20秒。"

5. [特殊技 1 - 腐蚀酸液 / SP1 Acid] (ID: 3182, pua_icon: 0xe41d, category: sp1)
   - 官方描述: "50%概率施加1层酸液减益，造成攻击力80%的伤害，持续10秒。"

6. [被动 - 特殊伤害蓄能 / Special Damage Charge] (ID: 3183, pua_icon: 0xe41c, category: passive)
   - 官方描述: "每5秒获得一个特殊伤害增益，增加27%的特殊伤害，最大叠加6层。"

7. [被动 - 暴击伤害蓄能 / Crit Damage Charge] (ID: 3184, pua_icon: 0xe406, category: passive)
   - 官方描述: "在拥有6层特殊伤害后，每5秒获得一个暴击伤害增益，每1层增加18.9%的暴击伤害，最多叠加6层。"

8. [被动 - 特殊技消耗 / Special Attack Consume] (ID: 3185, category: passive)
   - 官方描述: "所有特殊技的最后一击命中时，消耗全部特殊技伤害和暴击伤害增益。"

9. [被动 - 破防暴击 / Debuff Crit Rate] (ID: 3186, pua_icon: 0xe406, category: passive)
   - 官方描述: "如果对方身上有伤害减益，所有攻击增加50%的暴击几率。"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_burn_statmod,
    make_crit_damage_statmod,
    make_crit_rate_statmod,
    validate_color_code,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "mixmaster_cin_rotf"


@register_bot(BOT_ID, name_zh="搅拌者", desc="破坏系重型化学炮手，酸液持续腐蚀、周期蓄能特殊伤害与暴伤、减益弱点击破暴击加成")
def build_mixmaster_abilities(base_hp: float = 32402.0, base_atk: float = 2306.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. SP2 燃烧 (ID: 3178): 100% ATK, 8s, 60%
    # -------------------------------------------------------------------------
    m1, a1 = make_burn_statmod(
        mod_id="mixmaster_s2_burn",
        duration=8.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    # -------------------------------------------------------------------------
    # 2. SP3 燃烧 (ID: 3179): 120% ATK, 8s, 70%
    # -------------------------------------------------------------------------
    m2, a2 = make_burn_statmod(
        mod_id="mixmaster_s3_burn",
        duration=8.0,
        total_dmg=float(round(base_atk * 1.20)),
        chance=0.70,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m2)
    appears.update(a2)

    # -------------------------------------------------------------------------
    # 3. 远程酸液 (ID: 3180): 远程第1/2击 30% 概率 45% ATK 持续 9 秒
    # -------------------------------------------------------------------------
    m_acid_rng, a_acid_rng = make_burn_statmod(
        mod_id="mixmaster_ranged_acid",
        duration=9.0,
        total_dmg=float(round(base_atk * 0.45)),
        chance=0.30,
        trigger="onHit",
        trigger_scope="level=Ranged",
        callout_text="酸液",
        stackable=True,
        pua_icon="\uE41D",
        color_hex="84CC16",
        gradient_bottom="4D7C0F",
    )
    mods.update(m_acid_rng)
    appears.update(a_acid_rng)

    # -------------------------------------------------------------------------
    # 4. SP3 酸液 (ID: 3181): 100% 概率 134% ATK 持续 20 秒
    # -------------------------------------------------------------------------
    m_acid_sp3, a_acid_sp3 = make_burn_statmod(
        mod_id="mixmaster_sp3_acid",
        duration=20.0,
        total_dmg=float(round(base_atk * 1.34)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        callout_text="强酸",
        stackable=True,
        pua_icon="\uE41D",
        color_hex="84CC16",
        gradient_bottom="4D7C0F",
    )
    mods.update(m_acid_sp3)
    appears.update(a_acid_sp3)

    # -------------------------------------------------------------------------
    # 5. SP1 酸液 (ID: 3182): 50% 概率 80% ATK 持续 10 秒
    # -------------------------------------------------------------------------
    m_acid_sp1, a_acid_sp1 = make_burn_statmod(
        mod_id="mixmaster_sp1_acid",
        duration=10.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=0.50,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        callout_text="酸液",
        stackable=True,
        pua_icon="\uE41D",
        color_hex="84CC16",
        gradient_bottom="4D7C0F",
    )
    mods.update(m_acid_sp1)
    appears.update(a_acid_sp1)

    # -------------------------------------------------------------------------
    # 6. 被动 - 特殊伤害蓄能 (ID: 3183): 每 5 秒获得 27% 特殊伤害，上限 6 层
    # -------------------------------------------------------------------------
    validate_color_code("FF8800", "spec_dmg_tc")
    validate_color_code("DD6600", "spec_dmg_gb")
    appr_spec = {
        "id": "appr_mixmaster_special_dmg",
        "a": "特殊伤害",
        "s": "特殊伤害",
        "l": "每5秒获得1层特殊伤害增益，提升特殊技伤害27%(上限6层)",
        "ss": "特殊伤害",
        "t": "\uE41C",
        "f": "",
        "st": "特殊伤害",
        "ps": "特殊伤害",
        "pl": "特殊伤害生效中",
        "tc": "FF8800",
        "gt": "FF8800",
        "gb": "DD6600",
    }
    validate_appear(appr_spec)
    appears["appr_mixmaster_special_dmg"] = appr_spec

    mod_spec = {
        "id": "mixmaster_special_dmg_buff",
        "t": "special_damage",
        "tm": "",
        "tr": ["always"],
        "uit": ["always"],
        "pri": 0,
        "trm": 5.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.27,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 6,
        "g": "special_damage",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_mixmaster_special_dmg"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_spec)
    mods["mixmaster_special_dmg_buff"] = mod_spec

    # -------------------------------------------------------------------------
    # 7. 被动 - 暴击伤害蓄能 (ID: 3184): 满层特殊伤害后每 5 秒获得 18.9% 暴伤，上限 6 层
    # -------------------------------------------------------------------------
    m_crit_dmg, a_crit_dmg = make_crit_damage_statmod(
        mod_id="mixmaster_crit_dmg_buff",
        duration=-1.0,
        crit_dmg_bonus=0.189,
        chance=1.0,
        trigger="always",
        trigger_scope="",
        appr_id="appr_mixmaster_crit_dmg",
        callout_text="暴击伤害",
        pua_icon="\uE406",
        color_hex="FF8800",
        gradient_bottom="DD6600",
    )
    m_crit_dmg["mixmaster_crit_dmg_buff"]["st"] = 6
    mods.update(m_crit_dmg)
    appears.update(a_crit_dmg)

    # -------------------------------------------------------------------------
    # 8. 被动 - 特殊技消耗 (ID: 3185): 特殊技末击命中消耗全部特殊伤害和暴伤增益
    # -------------------------------------------------------------------------
    mod_sp_consume1 = {
        "id": "mixmaster_consume_special_buffs",
        "t": "remove",
        "tm": "mixmaster_special_dmg_buff",
        "tr": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "uit": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp_consume1)
    mods["mixmaster_consume_special_buffs"] = mod_sp_consume1

    mod_sp_consume2 = {
        "id": "mixmaster_consume_crit_buffs",
        "t": "remove",
        "tm": "mixmaster_crit_dmg_buff",
        "tr": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "uit": ["onSpecial1Hit", "onSpecial2Hit", "onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp_consume2)
    mods["mixmaster_consume_crit_buffs"] = mod_sp_consume2

    # -------------------------------------------------------------------------
    # 9. 被动 - 破防暴击 (ID: 3186): 目标有伤害减益时暴击率 +50%
    # -------------------------------------------------------------------------
    m_debuff_crit, a_debuff_crit = make_crit_rate_statmod(
        mod_id="mixmaster_debuff_crit_rate",
        duration=0.0,
        crit_bonus=0.50,
        chance=1.0,
        trigger="always",
        trigger_scope="target_has_debuff=True",
        appr_id="appr_mixmaster_debuff_crit",
        callout_text="暴击几率",
        pua_icon="\uE406",
        color_hex="FF8800",
        gradient_bottom="DD6600",
    )
    mods.update(m_debuff_crit)
    appears.update(a_debuff_crit)

    return mods, appears, buffs
