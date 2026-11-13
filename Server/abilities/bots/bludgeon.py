#!/usr/bin/env python3
"""
Bot Ability Implementation: 雷震 (Bludgeon)
===========================================
Bot ID: bludgeon_gs_rd20
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Warrior)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 暴击流血] (ID: 2701, pua_icon: 0xe401, category: passive)
   - 官方描述: "暴击时有25%的概率触发流血，在5秒内造成攻击力120%的伤害。如果是特殊技中的剑刃暴击，概率+60% (85%)。"
   - 实现方案:
     a) bludgeon_normal_crit_bleed: 普通暴击 25% 几率造成 5 秒 120% ATK 流血。
     b) bludgeon_sp_crit_bleed: 特殊技剑刃暴击 85% 几率造成 5 秒 120% ATK 流血。

2. [被动 - 护甲增益] (ID: 2702, pua_icon: 0xe517, category: passive)
   - 官方描述: "当被对方暴击命中时，有60%的概率获得1层51%的护甲增益，持续7秒 //可叠加"
   - 实现方案:
     c) bludgeon_crit_struck_armor: 触发 onStruckCrit, 60% 概率获得 1 层 51% 护甲增益持续 7.0 秒 (可叠加)。

3. [被动 - 重击眩晕与刷新护甲] (ID: 2703, pua_icon: 0xe605, category: passive)
   - 官方描述: "重击命中有19%的概率眩晕，持续1.5秒；重击启动时立即刷新雷震身上所有护甲增益的倒计时。"
   - 实现方案:
     d) bludgeon_heavy_stun: 触发 onHit, level=Heavy, 19% 概率造成眩晕 1.5 秒。
     e) 由 skill_bludgeon.c 在 on_attack_start(重击) 时刷新所有 bludgeon_crit_struck_armor 持续时间。

4. [特殊技 1 - 流血] (ID: 2704, pua_icon: 0xe401, category: special_1)
   - 官方描述: "最后一击有50%的概率施加流血，造成攻击力50%的伤害，持续6秒。"
   - 实现方案:
     f) bludgeon_sp1_bleed: 触发 onHit, level=Special1;lastHit=True, 50% 概率造成 50% ATK 流血持续 6.0 秒。

5. [特殊技 2 - 眩晕] (ID: 2705, pua_icon: 0xe605, category: special_2)
   - 官方描述: "最后一击命中时：64%的概率造成眩晕，持续2.5秒。"
   - 实现方案:
     g) bludgeon_sp2_stun: 触发 onHit, level=Special2;lastHit=True, 64% 概率眩晕 2.5 秒。

6. [特殊技 3 - 眩晕] (ID: 2706, pua_icon: 0xe605, category: special_3)
   - 官方描述: "最后一击90%的概率造成眩晕，持续3.5秒。"
   - 实现方案:
     h) bludgeon_sp3_stun: 触发 onHit, level=Special3;lastHit=True, 90% 概率眩晕 3.5 秒。

7. [觉醒 - 钢铠法] (ID: 2707, pua_icon: 0xe404, category: signature)
   - 官方描述: "当雷震的近战攻击落空时，他摧毁对手的渴望变得更强，下一次暴击命中时增加250%暴击伤害。"
   - 实现方案:
     i) bludgeon_metallikato_crit_dmg: 黄色暴击伤害图标 (PUA: \\uE404)，+250% 暴击伤害。
     j) 由 skill_bludgeon.c 判定近战攻击挥空落空并赋予，出暴击时消耗。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_armor_up_statmod,
    make_stun_statmod,
    make_statmod_appearance,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "bludgeon_gs_rd20"


@register_bot(BOT_ID, name_zh="雷震", desc="格斗系武士，剑刃暴击流血、受击护甲、重击眩晕与钢铠法")
def build_bludgeon_abilities(base_hp: float = 40966.0, base_atk: float = 3245.0):
    mods = {}
    appears = {}
    buffs = {}

    total_bleed_dmg = float(round(base_atk * 1.20, 2))

    # -------------------------------------------------------------------------
    # 1. 剑刃暴击流血 (常规 25% 几率，特殊技 85% 几率, 5 秒 120% ATK)
    # -------------------------------------------------------------------------
    m_norm_bleed, a_norm_bleed = make_bleed_statmod(
        mod_id="bludgeon_normal_crit_bleed",
        duration=5.0,
        total_dmg=total_bleed_dmg,
        chance=0.25,
        trigger="onCrit",
        trigger_scope="level=Light,Medium,Heavy",
        appr_id="appr_bludgeon_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_norm_bleed)
    appears.update(a_norm_bleed)

    m_sp_bleed, a_sp_bleed = make_bleed_statmod(
        mod_id="bludgeon_sp_crit_bleed",
        duration=5.0,
        total_dmg=total_bleed_dmg,
        chance=0.85,
        trigger="onCrit",
        trigger_scope="level=Special1,Special2,Special3",
        appr_id="appr_bludgeon_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp_bleed)
    appears.update(a_sp_bleed)

    # -------------------------------------------------------------------------
    # 2. 受对方暴击命中时 60% 获得 1 层 51% 护甲增益 (持续 7 秒，可叠加)
    # -------------------------------------------------------------------------
    m_armor, a_armor = make_armor_up_statmod(
        mod_id="bludgeon_crit_struck_armor",
        duration=7.0,
        armor_bonus=0.51,
        chance=0.60,
        trigger="onStruckCrit",
        trigger_scope="",
        appr_id="appr_bludgeon_armor",
        callout_text="护甲",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_armor)
    appears.update(a_armor)

    # -------------------------------------------------------------------------
    # 3. 重击 19% 眩晕 1.5 秒
    # -------------------------------------------------------------------------
    m_heavy_stun, a_heavy_stun = make_stun_statmod(
        mod_id="bludgeon_heavy_stun",
        duration=1.5,
        chance=0.19,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_bludgeon_heavy_stun",
        callout_text="眩晕",
    )
    mods.update(m_heavy_stun)
    appears.update(a_heavy_stun)

    # -------------------------------------------------------------------------
    # 4. SP1 最后一击 50% 造成 50% ATK 流血 6 秒
    # -------------------------------------------------------------------------
    sp1_bleed_dmg = float(round(base_atk * 0.50, 2))
    m_sp1_bleed, a_sp1_bleed = make_bleed_statmod(
        mod_id="bludgeon_sp1_bleed",
        duration=6.0,
        total_dmg=sp1_bleed_dmg,
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Special1;lastHit=True",
        appr_id="appr_bludgeon_sp1_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp1_bleed)
    appears.update(a_sp1_bleed)

    # -------------------------------------------------------------------------
    # 5. SP2 最后一击 64% 眩晕 2.5 秒
    # -------------------------------------------------------------------------
    m_sp2_stun, a_sp2_stun = make_stun_statmod(
        mod_id="bludgeon_sp2_stun",
        duration=2.5,
        chance=0.64,
        trigger="onHit",
        trigger_scope="level=Special2;lastHit=True",
        appr_id="appr_bludgeon_sp2_stun",
        callout_text="眩晕",
    )
    mods.update(m_sp2_stun)
    appears.update(a_sp2_stun)

    # -------------------------------------------------------------------------
    # 6. SP3 最后一击 90% 眩晕 3.5 秒
    # -------------------------------------------------------------------------
    m_sp3_stun, a_sp3_stun = make_stun_statmod(
        mod_id="bludgeon_sp3_stun",
        duration=3.5,
        chance=0.90,
        trigger="onHit",
        trigger_scope="level=Special3;lastHit=True",
        appr_id="appr_bludgeon_sp3_stun",
        callout_text="眩晕",
    )
    mods.update(m_sp3_stun)
    appears.update(a_sp3_stun)

    # -------------------------------------------------------------------------
    # 7. 钢铠法 (Metallikato): 挥空获得 +250% 暴伤，下次暴击消耗
    # -------------------------------------------------------------------------
    appr_metallikato = make_statmod_appearance(
        appr_id="appr_bludgeon_metallikato",
        callout_text="钢铠法",
        desc="近战攻击落空激起毁灭渴望，下一次暴击命中获得 +250% 暴击伤害。",
        short_desc="钢铠法",
        pua_icon="\uE404",
        color=AbilityColor.YELLOW_STATUS,
    )
    mod_metallikato = {
        "id": "bludgeon_metallikato_crit_dmg",
        "t": "crit_damage",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 2.50,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "metallikato",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_bludgeon_metallikato"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_metallikato)
    mods["bludgeon_metallikato_crit_dmg"] = mod_metallikato
    appears["appr_bludgeon_metallikato"] = appr_metallikato

    return mods, appears, buffs
