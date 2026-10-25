#!/usr/bin/env python3
"""
Bot Ability Implementation: 亡灵天尊 (Necrotronus)
=================================================
Bot ID: necrotronus_gs_kabam
阵营: 霸天虎 (Decepticon) | 职业: 战士系 (Warrior)

【官方技能真理源对照 (来自 character_abilities 数据库与优先技能中枢)】：
-----------------------------------------------------------------------------
1. [ID: 3209] [被动 - 泰坦充能] (Titan Charges)
   - 官方描述: "所有攻击命中时，获得1层泰坦充能 // 浅紫色图标。每层泰坦充能增加1.5%的攻击力"
   - 实现方案:
     necrotronus_titan_charge: 命中累加充能，上限基础20层(觉醒提升至40层)，每层+1.5%攻击力。

2. [ID: 3210] [被动 - 势不可挡的力量] (Overwhelming Power)
   - 官方描述: "当泰坦充能达到20层时，进入势不可挡的力量模式 // 多一个红色E91A图标，无倒计时，不叠加，但泰坦充能的浅紫色计数器不消失，红图标在泰坦充能少于20的时候消失。进入此状态时，自身受到的近战伤害放大30%"
   - 实现方案:
     necrotronus_overwhelming_power: 达到20层时激活红标，受到近战伤害放大30%。

3. [ID: 3207] [被动 - 势不可挡流血] (Bleed)
   - 官方描述: "进入势不可挡的力量模式后，所有攻击100%概率施加流血，造成攻击力25%的伤害，持续6秒。流血不可叠加，如果对方正在流血，则刷新倒计时。"
   - 实现方案:
     necrotronus_overwhelming_bleed: 势不可挡激活时所有攻击100%挂6秒单层刷新流血(25% ATK)。

4. [ID: 3208] [被动 - 能量功率减益] (Power Rate Debuff)
   - 官方描述: "当对手比自己能量更多时，对手能量功率降低30% // 显示一个红色的图标，对手能量少于我方时减益消失"
   - 实现方案:
     necrotronus_power_rate_debuff: 动态比对双方当前能量，对手能量高于自己时施加-30%功率减益(红标E606)。

5. [ID: 3211] [被动 - 不可阻挡] (Unstoppable)
   - 官方描述: "对方发动特殊技时，我方有30%的概率获得不可阻挡增益，持续0.95秒"
   - 实现方案:
     necrotronus_unstoppable: 对方SP起手触发，30%概率获得0.95s霸体(黄色E915)。

6. [ID: 3212] [被动 - 重击暴击几率] (Heavy Crit Rate)
   - 官方描述: "重击命中时，每个泰坦充能增加1%的的暴击几率"
   - 实现方案:
     necrotronus_heavy_crit_rate: 重击检定时根据当前充能层数动态增幅暴击率。

7. [ID: 3213] [被动 - 规避克制] (Anti Evade)
   - 官方描述: "近战攻击降低对手20%的规避几率 //不是减益，是如果对方要对亡灵天尊的近战计算规避时，概率减少20% //无图标"
   - 实现方案:
     necrotronus_anti_evade: 近战规避检定时直接削减对手20%闪避率。

8. [ID: 3214] [SP1 - 跌倒并再次崛起] (Fall and Rise Again)
   - 官方描述: "60%概率得到30%的能量功率增益，持续6秒；技能命中消耗10层泰坦充能"
   - 实现方案:
     necrotronus_sp1_power_rate: 命中60%概率得30%功率增益6秒，并消耗10层充能。

9. [ID: 3199] [SP2 - 暴击几率] (Crit Rate)
   - 官方描述: "65%的概率得到20%的暴击几率增益，持续12秒；技能命中消耗15层泰坦充能"
   - 实现方案:
     necrotronus_sp2_crit_buff: 命中65%概率得20%暴击率增益12秒，并消耗15层充能。

10. [ID: 3200] [SP3 - 终极流血] (Bleed)
    - 官方描述: "85%概率施加流血，造成攻击力40%的伤害，持续7秒。技能命中消耗20层泰坦充能"
    - 实现方案:
      necrotronus_sp3_bleed: 命中85%概率挂40% ATK流血7秒，并消耗20层充能。

11. [ID: 3197] [觉醒能力 - 愤怒] (Outrage)
    - 官方描述: "泰坦充能最大值提升为40。当势不可挡的力量激活时，暴击伤害增加80.3%"
    - 实现方案:
      necrotronus_signature_outrage: 充能上限扩展至40，势不可挡激活时暴伤+80.3%。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "necrotronus_gs_kabam"


@register_bot(BOT_ID, name_zh="亡灵天尊", desc="战士系，泰坦充能体系、势不可挡模式、全攻击流血、能量压制与近战必中克制")
def build_necrotronus_abilities(base_hp: float = 35484.0, base_atk: float = 2519.0):
    """
    根据基准属性生成亡灵天尊专属全套能力修饰器。
    基准 5星50级 HP = 35484.0, ATK = 2519.0
    """
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. [ID: 3209] 泰坦充能 (Titan Charges)
    # -------------------------------------------------------------------------
    appr_titan_charge = make_statmod_appearance(
        appr_id="appr_necrotronus_titan_charge",
        callout_text="泰坦充能",
        desc="每次攻击命中获得1层充能，每层提升1.5%攻击力 (浅紫色图标)",
        pua_icon="\uE91A",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=False,
    )
    mod_titan_charge = {
        "id": "necrotronus_titan_charge",
        "t": "attack_rating",
        "tm": "",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.015,
        "d": -1.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 40,
        "g": "necrotronus_titan_charge",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_titan_charge"],
        "au": ["appr_necrotronus_titan_charge"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_titan_charge)
    validate_statmod(mod_titan_charge)
    appears[appr_titan_charge["id"]] = appr_titan_charge
    mods[mod_titan_charge["id"]] = mod_titan_charge

    # -------------------------------------------------------------------------
    # 2. [ID: 3210] 势不可挡的力量 (Overwhelming Power)
    # -------------------------------------------------------------------------
    appr_overwhelming = make_statmod_appearance(
        appr_id="appr_necrotronus_overwhelming_power",
        callout_text="势不可挡",
        desc="泰坦充能达到20层激活，受到近战伤害放大30% (红色图标)",
        pua_icon="\uE91A",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_overwhelming = {
        "id": "necrotronus_overwhelming_power",
        "t": "dmg_taken_melee",
        "tm": "",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 1,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.30,
        "d": -1.0,
        "s": "none",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "necrotronus_overwhelming_power",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_overwhelming_power"],
        "au": ["appr_necrotronus_overwhelming_power"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_overwhelming)
    validate_statmod(mod_overwhelming)
    appears[appr_overwhelming["id"]] = appr_overwhelming
    mods[mod_overwhelming["id"]] = mod_overwhelming

    # -------------------------------------------------------------------------
    # 3. [ID: 3207] 势不可挡模式·全攻击流血 (Overwhelming Bleed)
    # -------------------------------------------------------------------------
    bleed_dmg = base_atk * 0.25
    m_bleed, a_bleed = make_bleed_statmod(
        mod_id="necrotronus_overwhelming_bleed",
        duration=6.0,
        total_dmg=bleed_dmg,
        chance=1.0,
        trigger="",
        appr_id="appr_necrotronus_overwhelming_bleed",
        callout_text="流血",
        stackable=False,
    )
    m_bleed["necrotronus_overwhelming_bleed"]["tr"] = []
    m_bleed["necrotronus_overwhelming_bleed"]["uit"] = []
    mods.update(m_bleed)
    appears.update(a_bleed)

    # -------------------------------------------------------------------------
    # 4. [ID: 3208] 能量功率减益 (Power Rate Debuff)
    # -------------------------------------------------------------------------
    appr_power_debuff = make_statmod_appearance(
        appr_id="appr_necrotronus_power_rate_debuff",
        callout_text="能量压制",
        desc="对手能量多于自身时，能量获取功率降低30% (红色图标)",
        pua_icon="\uE606",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
    )
    mod_power_debuff = {
        "id": "necrotronus_power_rate_debuff",
        "t": "power_rate",
        "tm": "",
        "ta": "opponent",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.30,
        "d": -1.0,
        "s": "none",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "necrotronus_power_rate_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_power_rate_debuff"],
        "au": ["appr_necrotronus_power_rate_debuff"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_power_debuff)
    validate_statmod(mod_power_debuff)
    appears[appr_power_debuff["id"]] = appr_power_debuff
    mods[mod_power_debuff["id"]] = mod_power_debuff

    # -------------------------------------------------------------------------
    # 5. [ID: 3211] 不可阻挡霸体 (Unstoppable)
    # -------------------------------------------------------------------------
    appr_unstoppable = make_statmod_appearance(
        appr_id="appr_necrotronus_unstoppable",
        callout_text="不可阻挡",
        desc="对手释放特殊技时30%概率获得0.95秒不可阻挡",
        pua_icon="\uE915",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    mod_unstoppable = {
        "id": "necrotronus_unstoppable",
        "t": "unstoppable",
        "tm": "",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 1,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 0.30,
        "m": 1.0,
        "d": 0.95,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "necrotronus_unstoppable",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_unstoppable"],
        "au": ["appr_necrotronus_unstoppable"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_unstoppable)
    validate_statmod(mod_unstoppable)
    appears[appr_unstoppable["id"]] = appr_unstoppable
    mods[mod_unstoppable["id"]] = mod_unstoppable

    # -------------------------------------------------------------------------
    # 6. [ID: 3212] 重击暴击几率 (Heavy Crit Rate)
    # -------------------------------------------------------------------------
    appr_heavy_crit = make_statmod_appearance(
        appr_id="appr_necrotronus_heavy_crit_rate",
        callout_text="重击暴击",
        desc="重击命中时每个泰坦充能增加1%暴击几率",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=False,
    )
    mod_heavy_crit = {
        "id": "necrotronus_heavy_crit_rate",
        "t": "crit_rate",
        "tm": "",
        "ta": "self",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.01,
        "d": 0.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 40,
        "g": "necrotronus_heavy_crit_rate",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_heavy_crit_rate"],
        "au": ["appr_necrotronus_heavy_crit_rate"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_heavy_crit)
    validate_statmod(mod_heavy_crit)
    appears[appr_heavy_crit["id"]] = appr_heavy_crit
    mods[mod_heavy_crit["id"]] = mod_heavy_crit

    # -------------------------------------------------------------------------
    # 7. [ID: 3213] 规避克制 (Anti-Evade, 近战攻击降低对手20%规避几率，无图标)
    # -------------------------------------------------------------------------
    mod_anti_evade = {
        "id": "necrotronus_anti_evade",
        "t": "anti_evade",
        "tm": "",
        "ta": "self",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Melee",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.20,
        "d": -1.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "necrotronus_anti_evade",
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
    validate_statmod(mod_anti_evade)
    mods[mod_anti_evade["id"]] = mod_anti_evade

    # -------------------------------------------------------------------------
    # 8. [ID: 3214] SP1 - 能量功率 (跌倒并再次崛起)
    # -------------------------------------------------------------------------
    appr_sp1 = make_statmod_appearance(
        appr_id="appr_necrotronus_sp1_power_rate",
        callout_text="跌倒并再次崛起",
        desc="60%概率获得30%能量功率增益持续6秒，消耗10层泰坦充能",
        pua_icon="\uE606",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
    )
    mod_sp1 = {
        "id": "necrotronus_sp1_power_rate",
        "t": "power_rate",
        "tm": "",
        "ta": "self",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=1",
        "trr": "repeat",
        "c": 0.60,
        "m": 0.30,
        "d": 6.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "necrotronus_sp1_power_rate",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_sp1_power_rate"],
        "au": ["appr_necrotronus_sp1_power_rate"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_sp1)
    validate_statmod(mod_sp1)
    appears[appr_sp1["id"]] = appr_sp1
    mods[mod_sp1["id"]] = mod_sp1

    # -------------------------------------------------------------------------
    # 9. [ID: 3199] SP2 - 暴击几率 (Special Attack 2)
    # -------------------------------------------------------------------------
    appr_sp2 = make_statmod_appearance(
        appr_id="appr_necrotronus_sp2_crit_buff",
        callout_text="暴击专精",
        desc="65%概率获得20%暴击几率增益持续12秒，消耗15层泰坦充能",
        pua_icon="\uE40D",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=True,
    )
    mod_sp2 = {
        "id": "necrotronus_sp2_crit_buff",
        "t": "crit_rate",
        "tm": "",
        "ta": "self",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 1,
        "trm": 0.0,
        "trs": "special=2",
        "trr": "repeat",
        "c": 0.65,
        "m": 0.20,
        "d": 12.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "necrotronus_sp2_crit_buff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_sp2_crit_buff"],
        "au": ["appr_necrotronus_sp2_crit_buff"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_sp2)
    validate_statmod(mod_sp2)
    appears[appr_sp2["id"]] = appr_sp2
    mods[mod_sp2["id"]] = mod_sp2

    # -------------------------------------------------------------------------
    # 10. [ID: 3200] SP3 - 终极流血 (Ultimate Bleed)
    # -------------------------------------------------------------------------
    bleed_sp3_dmg = base_atk * 0.40
    m_sp3, a_sp3 = make_bleed_statmod(
        mod_id="necrotronus_sp3_bleed",
        duration=7.0,
        total_dmg=bleed_sp3_dmg,
        chance=0.85,
        trigger="onHit",
        trigger_scope="special=3",
        appr_id="appr_necrotronus_sp3_bleed",
        callout_text="终极流血",
        stackable=False,
    )
    mods.update(m_sp3)
    appears.update(a_sp3)

    # -------------------------------------------------------------------------
    # 11. [ID: 3197] 觉醒能力 - 愤怒 (Outrage)
    # -------------------------------------------------------------------------
    appr_signature = make_statmod_appearance(
        appr_id="appr_necrotronus_signature_outrage",
        callout_text="愤怒",
        desc="泰坦充能上限提升为40；势不可挡激活时暴击伤害增加80.3%",
        pua_icon="\uE906",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=False,
    )
    mod_signature = {
        "id": "necrotronus_signature_outrage",
        "t": "crit_damage",
        "tm": "",
        "ta": "self",
        "tr": [],
        "uit": [],
        "pri": 2,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.803,
        "d": -1.0,
        "s": "none",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "necrotronus_signature_outrage",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_necrotronus_signature_outrage"],
        "au": ["appr_necrotronus_signature_outrage"],
        "rh": 0.0,
        "ra": 0.0,
        "it": 0,
    }
    validate_appear(appr_signature)
    validate_statmod(mod_signature)
    appears[appr_signature["id"]] = appr_signature
    mods[mod_signature["id"]] = mod_signature

    return mods, appears, buffs
