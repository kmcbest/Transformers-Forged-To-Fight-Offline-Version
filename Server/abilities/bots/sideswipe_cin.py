#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影横炮 (Sideswipe ROTF)
======================================================
Bot ID: sideswipe_cin_rotf
阵营: 汽车人 (Autobot) | 职业: 格斗系 (Warrior)

【官方技能真理源对照 (来自 Upstash KV 数据库 sideswipe_cin_rotf)】：
-----------------------------------------------------------------------------
1. [觉醒技 - 我真酷！ / I'm So Cool!] (category: signature, PUA: 0xE906)
   - 官方描述: "主动闪避敌人的一次攻击时，获得1层180%的暴击伤害增益，使得他的下一次中等攻击（M1或M2）不可规避，命中时必定暴击。//多次闪避可叠加，直到下一次中等攻击命中"
   - 实现方案:
     sideswipe_cin_sig_cool: tr=[]，由 skill_sideswipe_cin.c 在主动后闪/侧闪躲过攻击后叠加；
     下一次 M1/M2 必定暴击、不可规避并按层数结算 +180%/层 暴击伤害，命中后清空层数。

2. [被动 - 暴击伤害增益] (category: passive, PUA: 0xE906)
   - 官方描述: "轻度或中度连击的最后一击（L4或M2）不可以被规避，必定暴击并提升180%暴击伤害//可与招牌的爆伤叠加，直接结算，无图标，无callout字"
   - 实现方案:
     由 skill_sideswipe_cin.c 精确识别 L4 / M2：不可规避、+100% 必暴、+180% 暴伤直接结算（无图标无 callout）。

3. [被动 - 远程规避] (category: passive, PUA: 0xE518)
   - 官方描述: "前冲或重击过程中有35%的概率穿透对方的基础远程和远程重击 // 参考风刃的重击，callout 同；如果没有触发穿透，则100%的概率触发规避 // callout绿字“规避”"
   - 实现方案:
     由 skill_sideswipe_cin.c on_ranged_pierce_check (35% 穿透) 与 on_evade_check (未穿透 100% 规避) 协同，
     触发规避时附加绿色“规避” Callout (sideswipe_cin_ranged_evade_callout)。

4. [被动 - 流血] (category: passive, PUA: 0xE401)
   - 官方描述: "近战暴击时，有45%的概率施加1层流血，造成攻击力65%的伤害，持续4秒。//包括重击暴击"
   - 实现方案:
     sideswipe_cin_crit_bleed: tr=[]，C 侧近战/重击暴击非格挡时 45% 施加 4.0s 流血 (65% ATK)。

5. [被动 - 暴击几率] (category: passive, PUA: 0xE40D)
   - 官方描述: "对正在流血的对手：所有攻击暴击几率提升24% //黄图标，对手有流血时出现，流血完全结束后消失"
   - 实现方案:
     sideswipe_cin_bleed_crit_rate: tr=[]，C 侧实时同步对手流血状态挂载/移除 +24% 暴击率黄图标。

6. [SP1 - 挑斩] (category: sp1)
   - 驱散 (PUA: 无图标): "最后一击命中时有85%几率驱散对手的一个护甲增益。//技能无图标，触发成功时对方callout红字“护甲移除”"
   - 流血 (PUA: 0xE401): "最后一击暴击时100%几率施加流血，在2秒内造成攻击力125%的伤害。"
   - 暴击伤害增益 (PUA: 0xE906): "技能有效期增加75%的暴击伤害 // 黄图标，在技能结束后消失"
   - 规避克制 (PUA: 0xE92A): "技能全程不可被规避"

7. [SP2 - 落日斩] (category: sp2)
   - 流血 (PUA: 0xE401): "所有攻击暴击时100%几率施加流血，在4秒内造成攻击力100%的伤害。"
   - 暴击伤害增益 (PUA: 0xE906): "技能有效期增加75%的暴击伤害 // 黄图标，在技能结束后消失"
   - 规避克制 (PUA: 0xE92A): "技能全程不可被规避"

8. [SP3 - 不羁双刃] (category: sp3)
   - 流血 (PUA: 0xE401): "最后一击命中时施加1层史诗级流血，在10秒内造成攻击力150%的伤害。"
   - 暴击伤害增益 (PUA: 0xE906): "技能有效期增加75%的暴击伤害 // 黄图标，在技能结束后消失"
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_crit_damage_statmod,
    make_crit_rate_statmod,
    make_nullify_statmod,
    make_statmod_appearance,
    validate_appear,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "sideswipe_cin_rotf"


@register_bot(
    BOT_ID,
    name_zh="电影横炮",
    desc="格斗系双刃近战刺客，主动闪避叠层必暴、L4/M2终结暴击、前冲重击穿透规避远程、全段流血联动与SP爆发",
)
def build_sideswipe_cin_abilities(base_hp: float = 39343.0, base_atk: float = 3366.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. [觉醒技 - 我真酷！] 主动闪避获得可叠加 +180% 暴击伤害增益 (下一次 M1/M2 必定暴击、不可规避并消耗)
    m_cool, a_cool = make_crit_damage_statmod(
        mod_id="sideswipe_cin_sig_cool",
        duration=-1.0,
        crit_dmg_bonus=1.80,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_sig_cool",
        callout_text="暴击伤害增益",
        pua_icon="\uE906",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    m_cool["sideswipe_cin_sig_cool"]["st"] = 10
    m_cool["sideswipe_cin_sig_cool"]["g"] = "sideswipe_cin_cool"
    validate_statmod(m_cool["sideswipe_cin_sig_cool"])
    mods.update(m_cool)
    appears.update(a_cool)

    # 2. [被动 - 远程规避 Callout] 前冲或重击未触发 35% 穿透时，100% 触发绿色“规避” Callout
    appr_ranged_ev = make_statmod_appearance(
        appr_id="appr_sideswipe_cin_ranged_evade",
        callout_text="规避",
        desc="前冲或重击期间规避对手基础远程与远程重击",
        short_desc="远程规避",
        pua_icon="\uE518",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
    )
    mod_ranged_ev = {
        "id": "sideswipe_cin_ranged_evade_callout",
        "t": "evade_ranged",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 0.8,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "sideswipe_cin_ranged_evade",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_cin_ranged_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_ranged_ev)
    validate_appear(appr_ranged_ev)
    mods["sideswipe_cin_ranged_evade_callout"] = mod_ranged_ev
    appears["appr_sideswipe_cin_ranged_evade"] = appr_ranged_ev

    # 3. [被动 - 近战暴击流血] 近战暴击(含重击) 45% 施加 65% ATK 4 秒流血
    m_p_bleed, a_p_bleed = make_bleed_statmod(
        mod_id="sideswipe_cin_crit_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.65, 2)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_crit_bleed",
        callout_text="流血",
        stackable=True,
        pua_icon="\uE401",
    )
    mods.update(m_p_bleed)
    appears.update(a_p_bleed)

    # 4. [被动 - 流血目标暴击率 +24%] 黄图标，对手流血期间存在、结束后消失
    m_bleed_crit, a_bleed_crit = make_crit_rate_statmod(
        mod_id="sideswipe_cin_bleed_crit_rate",
        duration=-1.0,
        crit_bonus=0.24,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_bleed_crit_rate",
        callout_text="暴击几率",
        pua_icon="\uE40D",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    m_bleed_crit["sideswipe_cin_bleed_crit_rate"]["g"] = "sideswipe_cin_bleed_crit"
    validate_statmod(m_bleed_crit["sideswipe_cin_bleed_crit_rate"])
    mods.update(m_bleed_crit)
    appears.update(a_bleed_crit)

    # 5. [SP1 - 护甲移除驱散] 末击 85% 驱散对手 1 个护甲增益，仅弹对方红字“护甲移除”
    m_sp1_null, a_sp1_null = make_nullify_statmod(
        mod_id="sideswipe_cin_sp1_nullify",
        target_categories=["armor"],
        max_stacks_per_cat=1,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_sp1_nullify",
        callout_text="护甲移除",
        pua_icon="\uE950",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp1_null)
    appears.update(a_sp1_null)

    # 6. [SP1 - 末击暴击流血] 125% ATK 2 秒流血
    m_sp1_bleed, a_sp1_bleed = make_bleed_statmod(
        mod_id="sideswipe_cin_sp1_bleed",
        duration=2.0,
        total_dmg=float(round(base_atk * 1.25, 2)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_sp1_bleed",
        callout_text="流血",
        stackable=True,
        pua_icon="\uE401",
    )
    mods.update(m_sp1_bleed)
    appears.update(a_sp1_bleed)

    # 7. [SP2 - 暴击流血] 所有暴击命中 100% ATK 4 秒流血
    m_sp2_bleed, a_sp2_bleed = make_bleed_statmod(
        mod_id="sideswipe_cin_sp2_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.00, 2)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_sp2_bleed",
        callout_text="流血",
        stackable=True,
        pua_icon="\uE401",
    )
    mods.update(m_sp2_bleed)
    appears.update(a_sp2_bleed)

    # 8. [SP3 - 史诗级流血] 末击命中 150% ATK 10 秒流血
    m_sp3_bleed, a_sp3_bleed = make_bleed_statmod(
        mod_id="sideswipe_cin_sp3_bleed",
        duration=10.0,
        total_dmg=float(round(base_atk * 1.50, 2)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_sp3_bleed",
        callout_text="流血",
        stackable=True,
        pua_icon="\uE401",
    )
    mods.update(m_sp3_bleed)
    appears.update(a_sp3_bleed)

    # 9. [SP1/2/3 - 技能期暴击伤害 +75%] 黄图标，进入 SP 挂载、退出 SP 立即消失
    m_sp_cdmg, a_sp_cdmg = make_crit_damage_statmod(
        mod_id="sideswipe_cin_sp_crit_dmg",
        duration=6.0,
        crit_dmg_bonus=0.75,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_sideswipe_cin_sp_crit_dmg",
        callout_text="暴击伤害增益",
        pua_icon="\uE906",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    m_sp_cdmg["sideswipe_cin_sp_crit_dmg"]["g"] = "sideswipe_cin_sp_crit"
    validate_statmod(m_sp_cdmg["sideswipe_cin_sp_crit_dmg"])
    mods.update(m_sp_cdmg)
    appears.update(a_sp_cdmg)

    # 10. [SP1/2 - 规避克制] 技能全程不可被规避，黄图标 E92A，退出 SP 立即消失
    appr_sp_anti = make_statmod_appearance(
        appr_id="appr_sideswipe_cin_sp_anti_evade",
        callout_text="规避克制",
        desc="特殊技全程不可被规避",
        short_desc="规避克制",
        pua_icon="\uE92A",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=False,
    )
    mod_sp_anti = {
        "id": "sideswipe_cin_sp_anti_evade",
        "t": "anti_evade",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "sideswipe_cin_sp_anti",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_sideswipe_cin_sp_anti_evade"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp_anti)
    validate_appear(appr_sp_anti)
    mods["sideswipe_cin_sp_anti_evade"] = mod_sp_anti
    appears["appr_sideswipe_cin_sp_anti_evade"] = appr_sp_anti

    return mods, appears, buffs
