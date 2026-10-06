#!/usr/bin/env python3
"""
Bot Ability Implementation: 阿尔茜 (Arcee)
=========================================
Bot ID: arcee_gs_deluxe2014
阵营: 汽车人 (Autobot) | 职业: 勇士系 / 侦察兵 (Warrior / Scout)

【官方技能真理源对照 (来自 character_abilities 数据库与在线优先实现)】：
-----------------------------------------------------------------------------
1. [被动 - 爆头 / Head Shot] (pua_icon: 0xe401)
   - 官方描述: "远距离攻击有 50% 几率造成爆头，立刻造成 60% 攻击力，并在 3 秒内造成相当于 60% 攻击力的流血伤害。"
   - 实现方案:
     a) arcee_headshot_direct: 触发 onCrit，限制 level=Ranged,Special1，造成 60% ATK 额外直伤。
     b) arcee_headshot_dot: 触发 onCrit，限制 level=Ranged,Special1 且目标非冲刺 (opponent:state!=Dash,Run)，
        造成 60% ATK 流血伤害持续 3.0 秒。呼出文字: "BLEED"。

2. [被动 - 冲锋反制 / Headshot Rush]
   - 官方描述: "对处于前冲或奔跑状态的敌人造成爆头时，100% 造成极速流血。"
   - 实现方案:
     c) arcee_headshot_rush: 触发 onCrit，限制 level=Ranged,Special1 且目标正在冲刺 (opponent:state=Dash,Run)，
        100% 概率施加 3 秒流血。呼出文字: "HEADSHOT"。

3. [SP1 - 特技射击 / Trick Shot] (pua_icon: 0xe41b)
   - 官方描述: "远程伤害提升35%，远程射速提升20%，持续6.5秒"
   - 实现方案:
     d) arcee_sp1_trick_shot: 调用通用远程增益 make_ranged_boost_statmod(damage_bonus=0.35, speed_bonus=0.20, duration=6.5)

4. [SP2 - 致命核心/黑寡妇 / Femme's Fatality] (pua_icon: 0xe401)
   - 官方描述: "如果暴击，100%触发流血，4秒内造成攻击力108%的伤害。"
   - 实现方案:
     e) arcee_s2_bleed: 触发 onCrit，限制 level=Special2，造成 108% ATK 流血伤害持续 4.0 秒。呼出文字: "BLEED"。

5. [SP3 - 狙击 / Snipe] (pua_icon: 0xe401)
   - 官方描述: "100%概率触发爆头射击，立即造成攻击力135%的伤害，并在9秒内造成攻击力135%的流血伤害。"
   - 实现方案:
     f) arcee_sp3_snipe_direct: 触发 onSpecial3Activate，立即造成 135% ATK 直伤。
     g) arcee_sp3_snipe_bleed: 触发 onSpecial3Activate，造成 135% ATK 流血伤害持续 9.0 秒。呼出文字: "SNIPE"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod, make_direct_dmg_statmod, make_ranged_boost_statmod
from ..registry import register_bot

BOT_ID = "arcee_gs_deluxe2014"


@register_bot(BOT_ID, name_zh="阿尔茜", desc="爆头直伤与流血、冲锋反制、SP1特技射击远程增益与SP3狙击")
def build_arcee_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成阿尔茜全部专属能力修饰器。
    基准 5星50级 ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 阿尔茜爆头即时直接伤害 (Direct instant damage)
        "dmg_direct": {
            "id": "dmg_direct",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.60)),
            "c": 1,
            "value": float(round(base_atk * 0.60)),
            "buffType": "damage",
            "group": "dmg_direct",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 0.5},
            "loc_name": "headshot_direct",
            "loc_desc": "headshot_direct",
        },
        # 阿尔茜爆头流血 3 秒 DOT (3.0s Bleed DOT)
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.60)),
            "c": 1,
            "value": float(round(base_atk * 0.60)),
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 3.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
        # 阿尔茜 S2 暴击流血 4 秒 DOT (4.0s Bleed DOT)
        "dmg_bleed_s2": {
            "id": "dmg_bleed_s2",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 1.08)),
            "c": 1,
            "value": float(round(base_atk * 1.08)),
            "buffType": "damage",
            "group": "dmg_bleed",
            "p": {"damage_type": "bleed"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 4.0},
            "loc_name": "bleed",
            "loc_desc": "bleed",
        },
    }

    # ==========================================
    # 1. 保留原有被动能力：爆头与冲锋反制
    # ==========================================
    # (1) 爆头直接扣血 (60% ATK: 3485 * 0.6 = 2091)
    # (1) 爆头直接扣血 (60% ATK: 3485 * 0.6 = 2091)
    # 限制为飞弹/射击判定 (dmgFlags=Projectile)，排除 SP1 起手踢击
    m1, a1 = make_direct_dmg_statmod(
        mod_id="arcee_headshot_direct",
        dmg=base_atk * 0.60,
        chance=0.5,
        trigger="onCrit",
        trigger_scope="dmgFlags=Projectile;level=Ranged,Special1",
        buff_id="dmg_direct",
    )
    mods.update(m1)
    appears.update(a1)

    # (2) 爆头流血 3 秒 DOT (60% ATK, 50% 几率, 敌非前冲状态)
    # 限制为飞弹/射击判定 (dmgFlags=Projectile)，排除 SP1 起手踢击
    m2, a2 = make_bleed_statmod(
        mod_id="arcee_headshot_dot",
        duration=3.0,
        total_dmg=base_atk * 0.60,
        chance=0.5,
        trigger="onCrit",
        trigger_scope="dmgFlags=Projectile;level=Ranged,Special1;opponent:state!=Dash,Run",
        appr_id="appr_arcee_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m2)
    appears.update(a2)

    # (3) 爆头冲锋反制 3 秒流血 (60% ATK, 100% 必发, 敌处于 Dash/Run 状态)
    # 限制为飞弹/射击判定 (dmgFlags=Projectile)，排除 SP1 起手踢击
    m3, a3 = make_bleed_statmod(
        mod_id="arcee_headshot_rush",
        duration=3.0,
        total_dmg=base_atk * 0.60,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="dmgFlags=Projectile;level=Ranged,Special1;opponent:state=Dash,Run",
        appr_id="appr_arcee_headshot",
        callout_text="爆头",
        buff_id="dmg_bleed",
    )
    mods.update(m3)
    appears.update(a3)

    # ==========================================
    # 2. 特殊技 1 (SP1): 特技射击远程增益
    # ==========================================
    # 远程伤害提升 35%，远程射速/开枪速度提升 40%，持续 6.5 秒
    # 采用通用远程增益工厂，正向暖橙色 Buff，可被驱散
    m_sp1, a_sp1 = make_ranged_boost_statmod(
        mod_id="arcee_sp1_trick_shot",
        duration=6.5,
        damage_bonus=0.35,
        speed_bonus=0.40,
        trigger="onSpecial1Hit",
        trigger_scope="",
        appr_id="appr_arcee_sp1_boost",
        callout_text="特技射击",
        pua_icon="\uE41B",
        color_hex="FFAA00",
        gradient_bottom="FF6600",
    )
    mods.update(m_sp1)
    appears.update(a_sp1)

    # ==========================================
    # 3. 特殊技 2 (SP2): 致命核心暴击流血
    # ==========================================
    # S2 暴击流血 4 秒 DOT (108% ATK: 3485 * 1.08 = 3764, 100% 几率)
    m_sp2, a_sp2 = make_bleed_statmod(
        mod_id="arcee_s2_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.08)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special2",
        appr_id="appr_arcee_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp2)
    appears.update(a_sp2)

    # ==========================================
    # 4. 特殊技 3 (SP3): 狙击爆头直伤 + 9 秒流血
    # ==========================================
    # 前两击为体术踢腿 (index 0, 1) 不触发，后续4发手枪及1发狙击 (index 2..6) 触发
    # (1) SP3 爆头直接额外伤害 135% ATK
    m_sp3_dir, a_sp3_dir = make_direct_dmg_statmod(
        mod_id="arcee_sp3_snipe_direct",
        dmg=float(round(base_atk * 1.35)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="index!=0,1",
        buff_id="dmg_direct",
    )
    mods.update(m_sp3_dir)
    appears.update(a_sp3_dir)

    # (2) SP3 爆头流血 9 秒 DOT 135% ATK
    m_sp3_dot, a_sp3_dot = make_bleed_statmod(
        mod_id="arcee_sp3_snipe_bleed",
        duration=9.0,
        total_dmg=float(round(base_atk * 1.35)),
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="index!=0,1",
        appr_id="appr_arcee_sp3_bleed",
        callout_text="狙击",
        pua_icon="\uE401",
        buff_id="dmg_bleed",
    )
    mods.update(m_sp3_dot)
    appears.update(a_sp3_dot)

    return mods, appears, buffs
