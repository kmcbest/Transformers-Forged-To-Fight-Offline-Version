#!/usr/bin/env python3
"""
Bot Ability Implementation: 录音机 (Blaster)
===========================================
Bot ID: blaster_gs_leader2016
阵营: 汽车人 (Autobot) | 职业: 爆破系 / 科技系 (Blaster / Demolition / Tech)

【官方技能真理源对照 (来自 character_abilities 数据库与在线优先实现)】：
-----------------------------------------------------------------------------
1. [觉醒技 - 吸收护盾 / Absorption Shield] (ID: 2409)
   - 官方描述: "护盾状态下，录音机对远程攻击拥有不可阻挡的状态  // 打中只吃伤害无受创硬直，类似汽车大师的不可阻挡，但是身上不带光圈
     护盾额外提供20%的伤害减免"
   - 实现方案:
     a) blaster_sig_absorb_unstoppable: 护盾状态下受到远程攻击拥有不可阻挡状态 (无光圈)。
     b) blaster_sig_absorb_dr: 护盾状态下额外提供 20% 伤害减免 (armor_up)。

2. [被动 - 放大充能 / Amp Charge] (ID: 2419, pua_icon: E119)
   - 官方描述: "发动任意特殊技时，获得1层放大充能，最多叠加10层。//无倒计时
     每层放大充能增加6%的远程伤害，包括普通远程，重击和特殊技中的远程攻击"
   - 实现方案:
     c) blaster_amp_charge: 发动 SP1/SP2/SP3 时获得 1 层常驻放大充能 (最高叠加 10 层)，每层提升 6% 远程攻击伤害。

3. [被动 - 干扰 / Interference] (ID: 2420, pua_icon: E519)
   - 官方描述: "普通远程攻击命中或被防时，有80%概率施加干扰减益，降低对手远程攻击20%的伤害，50%的射速，持续10秒。//最大1层，可刷新"
   - 实现方案:
     d) blaster_interference: 普通远程命中或被格挡时 80% 几率施加干扰减益，降低对手 20% 远程伤害与 50% 射速，持续 10 秒。

4. [被动 - 震击 / Shock] (ID: 2421, pua_icon: 0xe914)
   - 官方描述: "重击命中100%的概率施加震击，造成攻击30%的伤害，持续5秒。
     每层放大充能增加20%的震击伤害"
   - 实现方案:
     e) blaster_heavy_shock: 重击命中 100% 施加 5 秒震击 DOT，造成基准 30% ATK 能量伤害，并根据放大充能层数提升伤害。

5. [被动 - 护盾 / Shield] (ID: 2422, pua_icon: E515)
   - 官方描述: "进入防御姿态时得到一个护盾，护盾生效时使受到的伤害降低15%，松开防御后0.5秒后护盾消失，每个放大充能延长倒计时0.25秒。
     //用例，10个放大充能，松开防御后倒计时为0.25*10+0.5=3秒"
   - 实现方案:
     f) blaster_block_shield: 进入防御姿态获得音波护盾，减伤 15%，松开防御基础维持 0.5 秒，放大充能动态延长。

6. [觉醒技 - 回血 / Repair] (ID: 2423, pua_icon: E503)
   - 官方描述: "护盾状态下，受到远程攻击和远程重击时，有40%的概率立即修复对手攻击力17%的生命值。如果受到的是特殊攻击，则修复34%。"
   - 实现方案:
     g) blaster_sig_repair_basic: 护盾状态受到远程攻击/重击，40% 几率修复对手 17% ATK 的生命值。
     h) blaster_sig_repair_special: 护盾状态受到远程特殊技，40% 几率修复对手 34% ATK 的生命值。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_shock_statmod,
    make_armor_up_statmod,
    make_heal_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "blaster_gs_leader2016"


@register_bot(
    BOT_ID,
    name_zh="录音机",
    desc="爆破系高能音频大师，吸收护盾远程霸体与高额减伤，特殊技叠加放大充能，远程干扰弱化敌方火力，重击致命震击，护盾受击紧急修复自愈",
)
def build_blaster_abilities(
    base_hp: float = 34850.0,
    base_atk: float = 3485.0,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    根据基准属性生成录音机 (Blaster) 全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 录音机震击能量伤害 DOT 模板
        "dmg_shock": {
            "id": "dmg_shock",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.30)),
            "c": 1,
            "value": float(round(base_atk * 0.30)),
            "buffType": "damage",
            "group": "dmg_shock",
            "p": {"damage_type": "energy"},
            "hasDuration": True,
            "e": 0,
            "time": {"amount": 5.0},
            "loc_name": "shock",
            "loc_desc": "shock",
        },
        # 录音机吸收护盾受击自愈模板
        "heal_absorb": {
            "id": "heal_absorb",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": float(round(base_atk * 0.17)),
            "c": 1,
            "value": float(round(base_atk * 0.17)),
            "buffType": "heal",
            "group": "heal",
            "p": {},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0.0},
            "loc_name": "repair",
            "loc_desc": "repair",
        },
    }

    # =========================================================================
    # 1. 觉醒技 - 吸收护盾 (ID: 2409): 护盾状态远程霸体 + 20% 额外减伤
    # =========================================================================
    # (1) 远程不可阻挡 (不带光圈 play_vfx=False)
    appr_absorb_unstoppable = make_statmod_appearance(
        appr_id="appr_blaster_absorb_unstoppable",
        callout_text="吸收护盾",
        desc="护盾生效期间对远程攻击拥有不可阻挡状态",
        pua_icon="\uE515",
        color=AbilityColor.BLUE_DEFENSE,
        show_callout=True,
    )
    mod_absorb_unstoppable = {
        "id": "blaster_sig_absorb_unstoppable",
        "t": "unstoppable",
        "tm": "",
        "tr": ["onTakeDamage"],
        "uit": ["onTakeDamage"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged,Heavy;dmgFlags=Projectile;self.status=armor_up",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "unstoppable",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blaster_absorb_unstoppable"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_absorb_unstoppable)
    validate_appear(appr_absorb_unstoppable)
    mods["blaster_sig_absorb_unstoppable"] = mod_absorb_unstoppable
    appears["appr_blaster_absorb_unstoppable"] = appr_absorb_unstoppable

    # (2) 护盾额外 20% 减伤
    m_absorb_dr, a_absorb_dr = make_armor_up_statmod(
        mod_id="blaster_sig_absorb_dr",
        duration=0.5,
        armor_bonus=0.20,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_blaster_absorb_dr",
        callout_text="吸收减免",
        pua_icon="\uE515",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        show_callout=False,
    )
    mods.update(m_absorb_dr)
    appears.update(a_absorb_dr)

    # =========================================================================
    # 2. 被动 - 放大充能 (ID: 2419): 发动特殊技获得1层放大充能(最多10层,无倒计时), 每层+6%远程伤害
    # =========================================================================
    appr_amp_charge = make_statmod_appearance(
        appr_id="appr_blaster_amp_charge",
        callout_text="放大充能",
        desc="每层放大充能提升6%远程伤害(最高10层)",
        pua_icon="\uE119",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_amp_charge = {
        "id": "blaster_amp_charge",
        "t": "ranged_buff",
        "tm": "",
        "tr": ["onSpecial1Activate", "onSpecial2Activate", "onSpecial3Activate"],
        "uit": ["onSpecial1Activate", "onSpecial2Activate", "onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.06,
        "d": -1.0,  # 无倒计时常驻堆叠
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 10,  # 最多叠加 10 层
        "g": "ranged_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blaster_amp_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_amp_charge)
    validate_appear(appr_amp_charge)
    mods["blaster_amp_charge"] = mod_amp_charge
    appears["appr_blaster_amp_charge"] = appr_amp_charge

    # =========================================================================
    # 3. 被动 - 干扰 (ID: 2420): 普通远程攻击命中或被防 80% 施加干扰减益(降低20%伤害与50%射速)
    # =========================================================================
    appr_interference = make_statmod_appearance(
        appr_id="appr_blaster_interference",
        callout_text="干扰",
        desc="降低对手20%远程攻击伤害与50%射速，持续10秒",
        pua_icon="\uE519",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_interference = {
        "id": "blaster_interference",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onHit", "onBlockHit"],
        "uit": ["onHit", "onBlockHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged",
        "trr": "repeat",
        "c": 0.80,
        "m": -0.20,  # 降低 20% 伤害
        "d": 10.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,  # 最大 1 层可刷新
        "g": "interference_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blaster_interference"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "speed_reduction": 0.50,  # 降低 50% 射速
    }
    validate_statmod(mod_interference)
    validate_appear(appr_interference)
    mods["blaster_interference"] = mod_interference
    appears["appr_blaster_interference"] = appr_interference

    # =========================================================================
    # 4. 被动 - 震击 (ID: 2421): 重击命中 100% 概率施加 5 秒震击 DOT (30% 攻击力能量伤害)
    # =========================================================================
    m_shock, a_shock = make_shock_statmod(
        mod_id="blaster_heavy_shock",
        duration=5.0,
        total_dmg=float(round(base_atk * 0.30)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_blaster_shock",
        callout_text="震击",
        pua_icon="\uE914",
    )
    mods.update(m_shock)
    appears.update(a_shock)

    # =========================================================================
    # 5. 被动 - 护盾 (ID: 2422): 防御姿态获得护盾减免 15% 伤害，松开后基础维持 0.5 秒
    # =========================================================================
    m_shield, a_shield = make_armor_up_statmod(
        mod_id="blaster_block_shield",
        duration=0.5,
        armor_bonus=0.15,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_blaster_shield",
        callout_text="音波护盾",
        pua_icon="\uE515",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        stackable=False,
    )
    mods.update(m_shield)
    appears.update(a_shield)

    # =========================================================================
    # 6. 觉醒技 - 回血 (ID: 2423): 护盾状态受击 40% 概率修复生命值 (普攻/重击 17%, 特殊攻击 34%)
    # =========================================================================
    # (1) 受到远程普攻或远程重击时修复 17% 对手攻击力
    m_repair_basic, a_repair_basic = make_heal_statmod(
        mod_id="blaster_sig_repair_basic",
        duration=0.0,
        heal_amount=float(round(base_atk * 0.17)),
        chance=0.40,
        trigger="onTakeDamage",
        trigger_scope="level=Ranged,Heavy;dmgFlags=Projectile;self.status=armor_up",
        appr_id="appr_blaster_repair",
        callout_text="吸收修复",
        pua_icon="\uE503",
        buff_id="heal_absorb",
    )
    mods.update(m_repair_basic)
    appears.update(a_repair_basic)

    # (2) 受到特殊攻击时修复 34% 对手攻击力
    m_repair_special, a_repair_special = make_heal_statmod(
        mod_id="blaster_sig_repair_special",
        duration=0.0,
        heal_amount=float(round(base_atk * 0.34)),
        chance=0.40,
        trigger="onTakeDamage",
        trigger_scope="level=Special1,Special2,Special3;dmgFlags=Projectile;self.status=armor_up",
        appr_id="appr_blaster_repair",
        callout_text="吸收修复",
        pua_icon="\uE503",
        buff_id="heal_absorb",
    )
    mods.update(m_repair_special)
    appears.update(a_repair_special)

    return mods, appears, buffs
