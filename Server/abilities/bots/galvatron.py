#!/usr/bin/env python3
"""
Bot Ability Implementation: 惊破天 (Galvatron)
==============================================
Bot ID: galvatron_gs_voyager2016
阵营: 霸天虎 (Decepticon) | 职业: 破坏分子 (Demolitions)

【官方技能真理源对照 (来自 tools/new_bots_priority_specs.json 与 character_abilities)】：
-----------------------------------------------------------------------------
1. [ID: 3045 | 觉醒技 - 宇宙大帝的意志 / Will of Unicron] (pua_icon: \uE915)
   - 官方描述: "完全充能时，根据对手失去生命值的百分比*0.5的概率获得不可阻挡，持续6秒，并在6秒内获得30%的最大能量槽
                //用例：对手生命值剩50%，25%的概率获得不可阻挡。"
   - 实现方案:
     a) galvatron_unicron_unstoppable: 充能满时概率获得 6 秒不可阻挡霸体。深紫图标 (E915)。
     b) galvatron_unicron_power: 6 秒内获得 30% 最大能量 (90 点 Mana)。

2. [ID: 3054 | 被动 - 黑暗能量充能 / Dark Energy Charge] (pua_icon: \uE90A)
   - 官方描述: "在远程攻击的距离开始格挡，每0.065秒获得一层黑暗能量充能 //只叠加层数，没有倒计时
                在充能达到30之前，停止格挡会以每层0.065秒的速度失去充能
                充能达到30层之后，停止格挡不会失去充能，但6秒倒计时开始。
                充能过程中格挡精通增加20%
                //充能时惊破天身上有专属光效"
   - 实现方案:
     galvatron_dark_energy_charge: 格挡时汇聚黑暗能量，最高叠加 30 层，提升格挡精通 20%。深紫专属图标 (E90A)。

3. [ID: 3055 | 被动 - 远程伤害 / Ranged Damage] (pua_icon: \uE41B)
   - 官方描述: "每层黑暗能量充能提升远程攻击5%的伤害"
   - 实现方案:
     galvatron_dark_ranged_boost: 远程攻击根据黑暗能量层数提升伤害 (每层 5%)。深紫图标 (E41B)。

4. [ID: 3056 | 被动 - 暴击伤害 / Crit Damage] (pua_icon: \uE906)
   - 官方描述: "每层黑暗能量充能提升近战暴击5%的伤害"
   - 实现方案:
     galvatron_dark_crit_damage: 近战暴击根据黑暗能量层数提升暴击伤害 (每层 5%)。深紫图标 (E906)。

5. [ID: 3057 | 被动 - 暴击几率 / Crit Rate] (pua_icon: \uE40D)
   - 官方描述: "L4和M2命中时增加50%的暴击几率。//无图标，仅针对本次攻击本身"
   - 实现方案:
     galvatron_combo_crit_rate: 轻击连招终结 (L4) 与中击终结 (M2) 命中时提升 50% 暴击几率。无图标呼出。

6. [ID: 3058 | 被动 - 黑暗燃烧 / Dark Burn] (pua_icon: \uE810)
   - 官方描述: "重击命中时，每层黑暗能量充能有1.7%的概率消耗所有黑暗能量充能并施加黑暗燃烧，造成攻击力140%的即时伤害"
   - 实现方案:
     galvatron_heavy_dark_burn: 重击命中消耗黑暗能量，造成 140% ATK 黑暗燃烧能量直伤。深紫图标 (E810)。

7. [ID: 3059 | 特殊技 1 - 眩晕 / SP1 Stun] (pua_icon: \uE605)
   - 官方描述: "每层黑暗能量充能有2%的概率眩晕对手3秒"
   - 实现方案:
     galvatron_sp1_stun: SP1 最后一击根据暗能充能概率眩晕对手 3 秒。亮黄图标 (E605)。

8. [ID: 3060 | 特殊技 2 - 黑暗燃烧 / SP2 Dark Burn] (pua_icon: \uE810)
   - 官方描述: "技能发动时，暂停黑暗能量充能的倒计时，直到技能结束后，如果黑暗能量充能未被最后一击消耗，倒计时继续。
                最后一击命中时，每层黑暗能量充能有2%的概率消耗所有黑暗能量充能并施加黑暗燃烧，造成攻击力140%的即时伤害"
   - 实现方案:
     galvatron_sp2_dark_burn: SP2 最后一击判定，触发黑暗燃烧造成 140% ATK 即时伤害。深紫图标 (E810)。

9. [ID: 3048 | 特殊技 3 - 暗能爆发 / SP3 Dark Energy Blast & Burn] (pua_icon: \uE90A)
   - 官方描述: "技能发动时，暂停黑暗能量充能的倒计时。
                技能发动立即获得30个黑暗能量充能，无倒计时。
                最后一击命中时，每层黑暗能量充能有3.3%的概率消耗所有黑暗能量充能并施加黑暗燃烧，造成攻击力140%的即时伤害。
                //由于30*3.3%视为100%，最后一击必然消耗所有黑暗能量充能"
   - 实现方案:
     a) galvatron_sp3_charge_grant: 发动立即获得 30 层黑暗能量充能。
     b) galvatron_sp3_dark_burn: 最后一击 100% 消耗充能并造成 140% ATK 黑暗燃烧即时伤害。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_stun_statmod,
    make_unstoppable_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "galvatron_gs_voyager2016"


@register_bot(BOT_ID, name_zh="惊破天", desc="宇宙大帝的先驱破坏狂，远程格挡积蓄黑暗能量充能、轻重连招暴击强化、重击与SP2/SP3极效黑暗燃烧、SP1暗能击晕与宇宙大帝霸体觉醒")
def build_galvatron_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    """
    根据基准属性生成惊破天全部专属能力修饰器。
    基准 5星50级 HP = 34850.0, ATK = 3485.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 惊破天专属黑暗能量充能 Buff (Dark Energy Charge)
        "dark_energy_charge": {
            "id": "dark_energy_charge",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "dark_energy_charge",
            "p": {"block_proficiency": 0.20},
            "hasDuration": False,
            "e": 0,
            "time": {"amount": 0.0},
            "loc_name": "dark_energy_charge",
            "loc_desc": "dark_energy_charge",
        },
    }

    # -------------------------------------------------------------------------
    # 1. [ID: 3045] 觉醒技 - 宇宙大帝的意志 (满充能时根据对手损血概率获得霸体6s + 30%能量)
    # -------------------------------------------------------------------------
    # (1) 不可阻挡霸体 6.0 秒
    m_sig_unstoppable, a_sig_unstoppable = make_unstoppable_statmod(
        mod_id="galvatron_unicron_unstoppable",
        duration=6.0,
        trigger="onTypeActivate",
        trigger_scope="type=dark_energy_full",
        appr_id="appr_galvatron_unicron_unstoppable",
        callout_text="宇宙大帝的意志",
        pua_icon="\uE915",
        color_hex=AbilityColor.DARK_PURPLE_SPECIAL_TC,
        gradient_bottom=AbilityColor.DARK_PURPLE_SPECIAL_GB,
    )
    mods.update(m_sig_unstoppable)
    appears.update(a_sig_unstoppable)

    # (2) 6 秒内获得 30% 最大能量 (90 点 Mana)
    mod_sig_power = {
        "id": "galvatron_unicron_power",
        "t": "power_gain",
        "tm": "",
        "tr": ["onTypeActivate"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "type=dark_energy_full",
        "trr": "repeat",
        "c": 1.0,
        "m": 90.0,  # 30% 最大能量
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_gain_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sig_power)
    mods[mod_sig_power["id"]] = mod_sig_power

    # -------------------------------------------------------------------------
    # 2. [ID: 3054] 被动 - 黑暗能量充能 (格挡时获得暗能量，最高叠加30层，格挡精通+20%)
    # -------------------------------------------------------------------------
    appr_dark_charge = make_statmod_appearance(
        appr_id="appr_galvatron_dark_charge",
        callout_text="黑暗能量",
        desc="汇聚宇宙大帝黑暗能量充能，格挡精通提升20%，最高叠加30层",
        short_desc="黑暗能量",
        pua_icon="\uE90A",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
    )
    mod_dark_charge = {
        "id": "galvatron_dark_energy_charge",
        "t": "dark_energy_charge",
        "tm": "",
        "tr": ["onPlayerStateEnter"],
        "uit": ["onPlayerStateEnter"],
        "pri": 0,
        "trm": 0.0,
        "trs": "state=Block",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": -1.0,  # 常驻叠层
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 30,
        "g": "dark_energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_galvatron_dark_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_dark_charge)
    validate_statmod(mod_dark_charge)
    appears[appr_dark_charge["id"]] = appr_dark_charge
    mods[mod_dark_charge["id"]] = mod_dark_charge

    # -------------------------------------------------------------------------
    # 3. [ID: 3055] 被动 - 远程伤害加成 (每层黑暗能量提升远程攻击5%伤害)
    # -------------------------------------------------------------------------
    appr_ranged_boost = make_statmod_appearance(
        appr_id="appr_galvatron_ranged_boost",
        callout_text="暗能加成",
        desc="每层黑暗能量充能提升远程伤害5%",
        short_desc="暗能加成",
        pua_icon="\uE41B",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
    )
    mod_ranged_boost = {
        "id": "galvatron_dark_ranged_boost",
        "t": "ranged_buff",
        "tm": "",
        "tr": ["onAttack"],
        "uit": ["onAttack"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Ranged",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 30,
        "g": "ranged_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_galvatron_ranged_boost"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_ranged_boost)
    validate_statmod(mod_ranged_boost)
    appears[appr_ranged_boost["id"]] = appr_ranged_boost
    mods[mod_ranged_boost["id"]] = mod_ranged_boost

    # -------------------------------------------------------------------------
    # 4. [ID: 3056] 被动 - 暴击伤害加成 (每层黑暗能量提升近战暴击5%伤害)
    # -------------------------------------------------------------------------
    appr_crit_dmg = make_statmod_appearance(
        appr_id="appr_galvatron_crit_damage",
        callout_text="暗能暴伤",
        desc="每层黑暗能量充能提升近战暴击伤害5%",
        short_desc="暗能暴伤",
        pua_icon="\uE906",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
    )
    mod_crit_dmg = {
        "id": "galvatron_dark_crit_damage",
        "t": "crit_damage",
        "tm": "",
        "tr": ["onCrit"],
        "uit": ["onCrit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light,Medium,Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.05,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 30,
        "g": "crit_damage",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_galvatron_crit_damage"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_crit_dmg)
    validate_statmod(mod_crit_dmg)
    appears[appr_crit_dmg["id"]] = appr_crit_dmg
    mods[mod_crit_dmg["id"]] = mod_crit_dmg

    # -------------------------------------------------------------------------
    # 5. [ID: 3057] 被动 - 连招暴击几率 (L4和M2命中时增加50%暴击几率，无图标)
    # -------------------------------------------------------------------------
    mod_combo_crit = {
        "id": "galvatron_combo_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "tr": ["onAttack"],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "attackId=L4,M2",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.50,
        "d": 0.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "crit_rate",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],  # 官方规范：无图标，仅针对本次攻击
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_combo_crit)
    mods[mod_combo_crit["id"]] = mod_combo_crit

    # -------------------------------------------------------------------------
    # 6. [ID: 3058] 被动 - 黑暗燃烧 (重击命中消耗暗能，造成140%攻击力即时伤害)
    # -------------------------------------------------------------------------
    appr_dark_burn = make_statmod_appearance(
        appr_id="appr_galvatron_dark_burn",
        callout_text="黑暗燃烧",
        desc="消耗黑暗能量造成140%攻击力即时能量伤害",
        short_desc="黑暗燃烧",
        pua_icon="\uE810",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
    )
    mod_heavy_dark_burn = {
        "id": "galvatron_heavy_dark_burn",
        "t": "dmg_burn",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 0.51,  # 充能满时约 51% 概率
        "m": float(round(base_atk * 1.40)),
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "dmg_burn",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_galvatron_dark_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr_dark_burn)
    validate_statmod(mod_heavy_dark_burn)
    appears[appr_dark_burn["id"]] = appr_dark_burn
    mods[mod_heavy_dark_burn["id"]] = mod_heavy_dark_burn

    # -------------------------------------------------------------------------
    # 7. [ID: 3059] 特殊技 1 - 眩晕 (每层暗能2%概率，满层60%几率眩晕3秒)
    # -------------------------------------------------------------------------
    m_sp1_stun, a_sp1_stun = make_stun_statmod(
        mod_id="galvatron_sp1_stun",
        duration=3.0,
        chance=0.60,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_galvatron_sp1_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m_sp1_stun)
    appears.update(a_sp1_stun)

    # -------------------------------------------------------------------------
    # 8. [ID: 3060] 特殊技 2 - 黑暗燃烧 (最后一击消耗暗能，造成140%攻击力即时伤害)
    # -------------------------------------------------------------------------
    mod_sp2_dark_burn = {
        "id": "galvatron_sp2_dark_burn",
        "t": "dmg_burn",
        "tm": "",
        "tr": ["onSpecial2Hit"],
        "uit": ["onSpecial2Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 0.60,
        "m": float(round(base_atk * 1.40)),
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "dmg_burn",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_galvatron_dark_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_dark_burn)
    mods[mod_sp2_dark_burn["id"]] = mod_sp2_dark_burn

    # -------------------------------------------------------------------------
    # 9. [ID: 3048] 特殊技 3 - 暗能爆发 (立即获得30层暗能，最后一击100%触发140%黑暗燃烧)
    # -------------------------------------------------------------------------
    # (1) 发动时立即获得 30 层黑暗能量充能
    mod_sp3_charge = {
        "id": "galvatron_sp3_charge_grant",
        "t": "dark_energy_charge",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 30.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 30,
        "g": "dark_energy_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_galvatron_dark_charge"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_charge)
    mods[mod_sp3_charge["id"]] = mod_sp3_charge

    # (2) 最后一击 100% 消耗充能并施加 140% ATK 黑暗燃烧
    mod_sp3_dark_burn = {
        "id": "galvatron_sp3_dark_burn",
        "t": "dmg_burn",
        "tm": "",
        "tr": ["onSpecial3Hit"],
        "uit": ["onSpecial3Hit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": float(round(base_atk * 1.40)),
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "dmg_burn",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_galvatron_dark_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp3_dark_burn)
    mods[mod_sp3_dark_burn["id"]] = mod_sp3_dark_burn

    return mods, appears, buffs
