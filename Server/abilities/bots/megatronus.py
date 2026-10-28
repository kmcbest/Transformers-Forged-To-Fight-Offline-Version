#!/usr/bin/env python3
"""
Bot Ability Implementation: 震天尊 (Megatronus)
==============================================
Bot ID: megatronus_gs_kabam
阵营: 霸天虎 (Decepticon) | 职业: 破坏系 (Demolition)

【官方技能真理源对照 (来自 character_abilities 数据库与优先技能中枢)】：
-----------------------------------------------------------------------------
1. [ID: 1793029715892] [被动 - 火种源的能量] (Power from the Allspark)
   - 官方描述: "震天尊的攻击和受到攻击不产生能量，他每秒自动产生最大能量的1.2% // 属于完全独立的能量产生机制，与其他所有角色都不同。"
   - 实现方案:
     megatronus_allspark_power: 挂载火种源能量机制，常规回能倍率归零，底层时钟每秒自动为震天尊充能 1.2% 最大能量 (0.036 bars/s)。

2. [ID: 1793029715893] [被动 - 狂怒遗迹] (Relic of Fury)
   - 官方描述: "开局处于狂怒遗迹状态，此状态下攻击力提升60%，降低对手20%的格挡精通。每充满一格能量，切换到保存遗迹 // 橙色图标"
   - 实现方案:
     megatronus_relic_fury: 开局激活橙色E91A图标，命中伤害提升60%，破防对手格挡；每充盈 1 格能量交替切换至保存遗迹。

3. [ID: 1793029715894] [被动 - 保存遗迹] (Relic of Preservation)
   - 官方描述: "此状态下伤害抗性提升60%。此状态下，限制对方任何单次攻击的伤害上限为震天尊最大生命值的20%。每充满一格能量，切换到保存遗迹 // 蓝色图标"
   - 实现方案:
     megatronus_relic_preservation: 蓝色E91A图标，受击减伤60%，且任何单次伤害上限截断为震天尊最大生命值的20%；充满1格能量后交替切换。

4. [ID: 1793029715895] [被动 - 不朽遗迹] (Relic of Immortality)
   - 官方描述: "当震天尊生命值降到10%以下时，他会发光跃起震开对手并额外激活不朽遗迹，持续8秒，此期间震天尊免疫任何伤害 // 所有直接伤害，DOT伤害，逆火伤害等，结算值均为0。一局只能激活一次不朽遗迹，如果震天尊开局生命值少于10%，不朽遗迹不会激活。"
   - 实现方案:
     megatronus_relic_immortality: 降到10%血量以下时触发8秒绝对无敌(暗紫E91A)，免除所有伤害；单局限触发一次。

5. [ID: 1793029715896] [被动 - 暴击几率] (Crit Rate)
   - 官方描述: "L4和M2命中时增加40%的暴击几率。// 无图标，仅针对本次攻击本身"
   - 实现方案:
     megatronus_crit_rate: 轻击连招终结 L4 与中击连招终结 M2 结算时动态提升 40% 暴击率。

6. [ID: 1793029715897] [被动 - 黑暗燃烧] (Dark Burn)
   - 官方描述: "重击命中100%概率施加黑暗燃烧，造成攻击力40%的即时伤害"
   - 实现方案:
     megatronus_heavy_dark_burn: 重击最后一击命中时施加即时黑暗燃烧(红色E810)，造成 40% ATK 能量伤害。

7. [ID: 1793029715898] [SP1 - 破甲] (Armor Break)
   - 官方描述: "最后一击60%的概率施加破甲，移除对手一层护甲增益，施加30%的破甲减益，持续8秒"
   - 实现方案:
     megatronus_sp1_armor_break: SP1 最后一击命中 60% 概率移除护甲并施加 8 秒破甲(红色E516，-30% 护甲)。

8. [ID: 1793029715899] [SP1 - 能量窃取] (Power Steal)
   - 官方描述: "如果狂怒遗迹生效，最后一击有100%的概率窃取对手现有能量的35% // 立即结算，红色图标出现在对方侧，一闪而过"
   - 实现方案:
     megatronus_sp1_power_steal: 狂怒遗迹生效时，SP1 最后一击 100% 窃取对手 35% 现有能量(红色E607)。

9. [ID: 1793029715900] [SP2 - 不可防御] (Unblockable)
   - 官方描述: "最后一击不可防御"
   - 实现方案:
     megatronus_sp2_unblockable: SP2 最后一击强行穿透对手格挡(黄色E41F)。

10. [ID: 1793029715901] [SP2 - 生命窃取] (Life Steal)
    - 官方描述: "如果保存遗迹生效，第一击有100%概率窃取对手生命，相当于震天尊最大生命值的17.5% // 红色图标出现在对方侧，一闪而过，我方弹出“生命窃取”字样，立即结算；如果对方剩余生命值少于震天尊最大生命值的17.5%，则KO对方的同时震天尊依然获得最大生命值的17.5%的回血。"
    - 实现方案:
      megatronus_sp2_life_steal: 保存遗迹生效时，SP2 首击 100% 抽取对手 17.5% 震天尊最大生命值并全额回复自身(红色E503)。

11. [ID: 1793029715902] [SP3 - 黑暗燃烧] (Dark Burn)
    - 官方描述: "最后一击100%概率施加黑暗燃烧，造成攻击力200%的即时伤害"
    - 实现方案:
      megatronus_sp3_dark_burn: SP3 最后一击造成 200% ATK 即时能量伤害(红色E810)。

12. [ID: 1793029715903] [SP3 - 能量窃取] (Power Steal)
    - 官方描述: "如果狂怒遗迹生效，第一击有66%的概率窃取对手现有能量的35% // 立即结算，红色图标出现在对方侧，一闪而过"
    - 实现方案:
      megatronus_sp3_power_steal: 狂怒遗迹生效时，SP3 首击 66% 窃取对手 35% 现有能量。

13. [ID: 1793029715904] [SP3 - 生命窃取] (Life Steal)
    - 官方描述: "如果保存遗迹生效，第一击有66%概率窃取对手生命，相当于震天尊最大生命值的17.5%"
    - 实现方案:
      megatronus_sp3_life_steal: 保存遗迹生效时，SP3 首击 66% 抽取对手 17.5% 最大生命值并全额自愈。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "megatronus_gs_kabam"


@register_bot(BOT_ID, name_zh="震天尊", desc="破坏系，火种源自主充能、狂怒与保存遗迹交替、不朽绝对免伤与能量/生命双窃取")
def build_megatronus_abilities(base_hp: float = 35206.0, base_atk: float = 2375.0) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    根据基准属性生成震天尊专属全套能力修饰器。
    基准 5星50级 HP = 35206.0, ATK = 2375.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. [ID: 1793029715892] 火种源的能量 (Power from the Allspark)
    # -------------------------------------------------------------------------
    appr_allspark = make_statmod_appearance(
        appr_id="appr_megatronus_allspark_power",
        callout_text="火种源的能量",
        desc="攻击和受击不产生能量，每秒自动产生最大能量的1.2%",
        pua_icon="\uE608",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=False,
    )
    mod_allspark = {
        "id": "megatronus_allspark_power",
        "t": "power_rate",
        "tm": "",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 1,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -1.0, # 归零常规回能倍率
        "d": -1.0,
        "s": "none",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_allspark_power",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_allspark_power"],
        "au": ["appr_megatronus_allspark_power"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_allspark)
    validate_statmod(mod_allspark)
    appears[appr_allspark["id"]] = appr_allspark
    mods[mod_allspark["id"]] = mod_allspark

    # -------------------------------------------------------------------------
    # 2. [ID: 1793029715893] 狂怒遗迹 (Relic of Fury)
    # -------------------------------------------------------------------------
    appr_fury = make_statmod_appearance(
        appr_id="appr_megatronus_relic_fury",
        callout_text="狂怒遗迹",
        desc="攻击力提升60%，降低对手20%格挡精通；每充满一格能量切换为保存遗迹",
        pua_icon="\uE91A",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_fury = {
        "id": "megatronus_relic_fury",
        "t": "attack",
        "tm": "",
        "ta": "self",
        "tr": ["onStart"],
        "uit": ["onStart"],
        "pri": 2,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.60,
        "d": -1.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_relic_fury",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_relic_fury"],
        "au": ["appr_megatronus_relic_fury"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_fury)
    validate_statmod(mod_fury)
    appears[appr_fury["id"]] = appr_fury
    mods[mod_fury["id"]] = mod_fury

    # -------------------------------------------------------------------------
    # 3. [ID: 1793029715894] 保存遗迹 (Relic of Preservation)
    # -------------------------------------------------------------------------
    appr_pres = make_statmod_appearance(
        appr_id="appr_megatronus_relic_preservation",
        callout_text="保存遗迹",
        desc="伤害抗性提升60%，单次受击伤害上限限制为最大生命值的20%",
        pua_icon="\uE91A",
        color=AbilityColor.BLUE_DEFENSE,
        show_callout=True,
    )
    mod_pres = {
        "id": "megatronus_relic_preservation",
        "t": "armor",
        "tm": "",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 2,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.60,
        "d": -1.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_relic_preservation",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_relic_preservation"],
        "au": ["appr_megatronus_relic_preservation"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_pres)
    validate_statmod(mod_pres)
    appears[appr_pres["id"]] = appr_pres
    mods[mod_pres["id"]] = mod_pres

    # -------------------------------------------------------------------------
    # 4. [ID: 1793029715895] 不朽遗迹 (Relic of Immortality)
    # -------------------------------------------------------------------------
    appr_immort = make_statmod_appearance(
        appr_id="appr_megatronus_relic_immortality",
        callout_text="不朽遗迹",
        desc="生命值降至10%以下激活不朽遗迹8秒，期间完全免疫任何伤害",
        pua_icon="\uE91A",
        color=AbilityColor.WHITE_SPECIAL,
        show_callout=True,
    )
    mod_immort = {
        "id": "megatronus_relic_immortality",
        "t": "protection",
        "tm": "",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 3,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 8.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_relic_immortality",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_relic_immortality"],
        "au": ["appr_megatronus_relic_immortality"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_immort)
    validate_statmod(mod_immort)
    appears[appr_immort["id"]] = appr_immort
    mods[mod_immort["id"]] = mod_immort

    # -------------------------------------------------------------------------
    # 5. [ID: 1793029715896] 暴击几率 (Crit Rate on L4/M2)
    # -------------------------------------------------------------------------
    appr_crit = make_statmod_appearance(
        appr_id="appr_megatronus_crit_rate",
        callout_text="暴击专精",
        desc="L4和M2连招收尾命中时增加40%暴击几率",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=False,
    )
    mod_crit = {
        "id": "megatronus_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "ta": "self",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "light=4,medium=2",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.40,
        "d": 0.0,
        "s": "none",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_crit_rate",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_crit_rate"],
        "au": ["appr_megatronus_crit_rate"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_crit)
    validate_statmod(mod_crit)
    appears[appr_crit["id"]] = appr_crit
    mods[mod_crit["id"]] = mod_crit

    # -------------------------------------------------------------------------
    # 6. [ID: 1793029715897] 重击黑暗燃烧 (Dark Burn)
    # -------------------------------------------------------------------------
    appr_dark_burn = make_statmod_appearance(
        appr_id="appr_megatronus_dark_burn",
        callout_text="黑暗燃烧",
        desc="重击命中100%施加即时能量伤害",
        pua_icon="\uE810",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_heavy_burn = {
        "id": "megatronus_heavy_dark_burn",
        "t": "direct_damage",
        "tm": "",
        "ta": "opponent",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "heavy=1",
        "trr": "repeat",
        "c": 1.0,
        "m": base_atk * 0.40,
        "d": 0.0,
        "s": "none",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_heavy_dark_burn",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_dark_burn"],
        "au": ["appr_megatronus_dark_burn"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_dark_burn)
    validate_statmod(mod_heavy_burn)
    appears[appr_dark_burn["id"]] = appr_dark_burn
    mods[mod_heavy_burn["id"]] = mod_heavy_burn

    # -------------------------------------------------------------------------
    # 7. [ID: 1793029715898] SP1 破甲 (Armor Break)
    # -------------------------------------------------------------------------
    appr_armor_break = make_statmod_appearance(
        appr_id="appr_megatronus_sp1_armor_break",
        callout_text="破甲",
        desc="SP1最后一击60%概率破甲，移除护甲增益并降低30%护甲持续8秒",
        pua_icon="\uE516",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp1_armor_break = {
        "id": "megatronus_sp1_armor_break",
        "t": "armor_break",
        "tm": "",
        "ta": "opponent",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=1",
        "trr": "repeat",
        "c": 0.60,
        "m": -0.30,
        "d": 8.0,
        "s": "none",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_sp1_armor_break",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_sp1_armor_break"],
        "au": ["appr_megatronus_sp1_armor_break"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_armor_break)
    validate_statmod(mod_sp1_armor_break)
    appears[appr_armor_break["id"]] = appr_armor_break
    mods[mod_sp1_armor_break["id"]] = mod_sp1_armor_break

    # -------------------------------------------------------------------------
    # 8. [ID: 1793029715899] SP1 能量窃取 (Power Steal)
    # -------------------------------------------------------------------------
    appr_power_steal = make_statmod_appearance(
        appr_id="appr_megatronus_power_steal",
        callout_text="能量窃取",
        desc="狂怒遗迹生效时，窃取对手现有能量的35%",
        pua_icon="\uE607",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp1_power_steal = {
        "id": "megatronus_sp1_power_steal",
        "t": "power_steal",
        "tm": "",
        "ta": "opponent",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=1",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.35,
        "d": 0.0,
        "s": "none",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_sp1_power_steal",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_power_steal"],
        "au": ["appr_megatronus_power_steal"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_power_steal)
    validate_statmod(mod_sp1_power_steal)
    appears[appr_power_steal["id"]] = appr_power_steal
    mods[mod_sp1_power_steal["id"]] = mod_sp1_power_steal

    # -------------------------------------------------------------------------
    # 9. [ID: 1793029715900] SP2 不可防御 (Unblockable)
    # -------------------------------------------------------------------------
    appr_unblockable = make_statmod_appearance(
        appr_id="appr_megatronus_sp2_unblockable",
        callout_text="不可阻挡",
        desc="SP2 最后一击不可防御",
        pua_icon="\uE41F",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_sp2_unblockable = {
        "id": "megatronus_sp2_unblockable",
        "t": "unblockable",
        "tm": "",
        "ta": "self",
        "tr": ["onAttack"],
        "uit": ["onAttack"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=2",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_sp2_unblockable",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_sp2_unblockable"],
        "au": ["appr_megatronus_sp2_unblockable"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_unblockable)
    validate_statmod(mod_sp2_unblockable)
    appears[appr_unblockable["id"]] = appr_unblockable
    mods[mod_sp2_unblockable["id"]] = mod_sp2_unblockable

    # -------------------------------------------------------------------------
    # 10. [ID: 1793029715901] SP2 生命窃取 (Life Steal)
    # -------------------------------------------------------------------------
    appr_life_steal = make_statmod_appearance(
        appr_id="appr_megatronus_life_steal",
        callout_text="生命窃取",
        desc="保存遗迹生效时，窃取对手相当于震天尊最大生命值17.5%的生命",
        pua_icon="\uE503",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_sp2_life_steal = {
        "id": "megatronus_sp2_life_steal",
        "t": "life_steal",
        "tm": "",
        "ta": "self",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=2",
        "trr": "repeat",
        "c": 1.0,
        "m": base_hp * 0.175,
        "d": 0.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_sp2_life_steal",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_life_steal"],
        "au": ["appr_megatronus_life_steal"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_life_steal)
    validate_statmod(mod_sp2_life_steal)
    appears[appr_life_steal["id"]] = appr_life_steal
    mods[mod_sp2_life_steal["id"]] = mod_sp2_life_steal

    # -------------------------------------------------------------------------
    # 11. [ID: 1793029715902] SP3 黑暗燃烧 (Dark Burn)
    # -------------------------------------------------------------------------
    mod_sp3_burn = {
        "id": "megatronus_sp3_dark_burn",
        "t": "direct_damage",
        "tm": "",
        "ta": "opponent",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=3",
        "trr": "repeat",
        "c": 1.0,
        "m": base_atk * 2.00,
        "d": 0.0,
        "s": "none",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_sp3_dark_burn",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_dark_burn"],
        "au": ["appr_megatronus_dark_burn"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_statmod(mod_sp3_burn)
    mods[mod_sp3_burn["id"]] = mod_sp3_burn

    # -------------------------------------------------------------------------
    # 12. [ID: 1793029715903] SP3 能量窃取 (Power Steal)
    # -------------------------------------------------------------------------
    mod_sp3_power_steal = {
        "id": "megatronus_sp3_power_steal",
        "t": "power_steal",
        "tm": "",
        "ta": "opponent",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=3",
        "trr": "repeat",
        "c": 0.66,
        "m": 0.35,
        "d": 0.0,
        "s": "none",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_sp3_power_steal",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_power_steal"],
        "au": ["appr_megatronus_power_steal"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_statmod(mod_sp3_power_steal)
    mods[mod_sp3_power_steal["id"]] = mod_sp3_power_steal

    # -------------------------------------------------------------------------
    # 13. [ID: 1793029715904] SP3 生命窃取 (Life Steal)
    # -------------------------------------------------------------------------
    mod_sp3_life_steal = {
        "id": "megatronus_sp3_life_steal",
        "t": "life_steal",
        "tm": "",
        "ta": "self",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=3",
        "trr": "repeat",
        "c": 0.66,
        "m": base_hp * 0.175,
        "d": 0.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_sp3_life_steal",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatronus_life_steal"],
        "au": ["appr_megatronus_life_steal"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_statmod(mod_sp3_life_steal)
    mods[mod_sp3_life_steal["id"]] = mod_sp3_life_steal

    # -------------------------------------------------------------------------
    # 4b. 震天尊专属三大遗迹光环 Move 特效 (官方 moves.assetbundle 原生绑定)
    # -------------------------------------------------------------------------
    mod_fury_vfx = {
        "id": "megatronus_relic_fury_vfx",
        "t": "play_move",
        "tm": "relic_orange",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_relic_vfx",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_statmod(mod_fury_vfx)
    mods[mod_fury_vfx["id"]] = mod_fury_vfx

    mod_pres_vfx = {
        "id": "megatronus_relic_preservation_vfx",
        "t": "play_move",
        "tm": "relic_blue",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": -1.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_relic_vfx",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_statmod(mod_pres_vfx)
    mods[mod_pres_vfx["id"]] = mod_pres_vfx

    mod_immort_vfx = {
        "id": "megatronus_relic_immortality_vfx",
        "t": "play_move",
        "tm": "relic_white",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 8.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "megatronus_relic_vfx",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_statmod(mod_immort_vfx)
    mods[mod_immort_vfx["id"]] = mod_immort_vfx

    return mods, appears, buffs
