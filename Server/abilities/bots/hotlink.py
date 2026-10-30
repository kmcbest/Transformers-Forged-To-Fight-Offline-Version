#!/usr/bin/env python3
"""
Bot Ability Implementation: 热链接 (Hotlink)
===========================================
Bot ID: hotlink_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 破坏系 (Demolition / Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合清单)】：
-----------------------------------------------------------------------------
1. [基础 - 喷火推进] (ID: 3603, category: basic)
   - 官方描述: "重击喷出猛烈烈焰火海，击退敌人并施加持续燃烧。自身完全免疫燃烧效果。"
   - 实现方案:
     hotlink_burn_immune: 自身免疫燃烧减益 (burn_immunity)。

2. [被动 - 烈焰猛火与流血抗性] (ID: 3604, pua_icon: 0xe517, category: passive)
   - 官方描述: "重击命中 100% 概率施加燃烧减益，造成攻击力 60% 的伤害，持续 6 秒。当对手处于燃烧状态时，热链接的近战攻击命中 100% 刷新该燃烧减益的持续时间，且额外造成 25% 的近战物理伤害。热链接自身受到流血减益影响时，受到的流血伤害降低 30%。"
   - 实现方案:
     a) hotlink_heavy_burn: 重击命中 100% 施加 6 秒燃烧 DOT (60% ATK, PUA: \\uE517)。
     b) hotlink_burn_melee_boost: 对手燃烧时近战攻击额外造成 25% 伤害 (PUA: \\uE412)。

3. [觉醒技 - 熔岩充盈] (ID: 3605, pua_icon: 0xe412, category: signature)
   - 官方描述: "当生命值低于 50% 时触发：获得持续 6 秒的不可阻挡增益；且在此期间每次近战攻击命中处于燃烧状态的敌人时，额外获得一层 15% 的近战增益，持续 5 秒（上限 3 层）。"
   - 实现方案:
     a) hotlink_sig_unstoppable: 生命低于 50% 获得 6 秒不可阻挡 (PUA: \\uE915)。
     b) hotlink_sig_melee_stack: 期间近战命中燃烧敌人叠加 15% 近战增益 (上限 3 层, PUA: \\uE412)。

4. [SP1 - 高温喷流] (ID: 3606, pua_icon: 0xe41d, category: sp1)
   - 官方描述: "最后一击命中 100% 概率施加燃烧减益，造成攻击力 50% 的伤害，持续 5 秒；技能结束后自身获得一层 20% 的近战增益，持续 6 秒。"
   - 实现方案:
     a) hotlink_sp1_burn: 最后一击 100% 施加 5 秒燃烧 (50% ATK, PUA: \\uE41D)。
     b) hotlink_sp1_melee_buff: 技能结束后自身获得 20% 近战增益 6 秒 (PUA: \\uE412)。

5. [SP2 - 熔火投弹] (ID: 3607, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "每一击有 85% 概率施加燃烧减益，造成攻击力 70% 的伤害，持续 6 秒；并有 50% 概率造成眩晕，持续 1.5 秒。"
   - 实现方案:
     a) hotlink_sp2_burn: 每一击 85% 施加 6 秒燃烧 (70% ATK, PUA: \\uE41D)。
     b) hotlink_sp2_stun: 50% 概率造成 1.5 秒眩晕 (PUA: \\uE605)。

6. [SP3 - 烈焰地狱] (ID: 3608, pua_icon: 0xe915, category: sp3)
   - 官方描述: "最后一击 100% 概率施加燃烧减益，造成攻击力 100% 的伤害，持续 8 秒；技能结束后获得一层 30% 的护甲增益，持续 8 秒，以及持续 4 秒的不可阻挡增益。"
   - 实现方案:
     a) hotlink_sp3_burn: 最后一击 100% 施加 8 秒燃烧 (100% ATK, PUA: \\uE41D)。
     b) hotlink_sp3_armor: 技能结束后获得 30% 护甲增益 8 秒 (PUA: \\uE515)。
     c) hotlink_sp3_unstoppable: 技能结束后获得 4 秒不可阻挡 (PUA: \\uE915)。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_burn_statmod,
    make_stun_statmod,
    make_attack_boost_statmod,
    make_armor_up_statmod,
    make_unstoppable_statmod,
    make_statmod_appearance,
    validate_appear,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "hotlink_gs_leader2015"


@register_bot(BOT_ID, name_zh="热链接", desc="破坏系喷火猛兽，完全免疫燃烧、重击与特殊技连环火海、残血霸体狂暴熔岩近战增益")
def build_hotlink_abilities(base_hp: float = 33000.0, base_atk: float = 2400.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    mods = {}
    appears = {}

    # 1. 基础免疫燃烧 (ID: 3603)
    appr_burn_immune = make_statmod_appearance(
        appr_id="appr_hotlink_burn_immune",
        callout_text="燃烧免疫",
        desc="热链接周身环绕隔热装甲，完全免疫燃烧减益",
        pua_icon="\uE517",
        color=AbilityColor.ORANGE_DAMAGE,
        show_callout=False,
    )
    validate_appear(appr_burn_immune)
    appears[appr_burn_immune["id"]] = appr_burn_immune

    mod_burn_immune = {
        "id": "hotlink_burn_immune",
        "t": "passive",
        "ta": "self",
        "tr": ["onStart"],
        "trs": "",
        "uit": [],
        "c": 1.0,
        "d": -1.0,
        "m": 0.0,
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_burn_immune["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "eff": [{"t": "immunity", "v": "dmg_burn"}],
    }
    validate_statmod(mod_burn_immune)
    mods[mod_burn_immune["id"]] = mod_burn_immune

    # 2. 被动: 重击命中施加燃烧 (ID: 3604)
    burn_heavy_dmg = base_atk * 0.60
    m_heavy_burn, a_heavy_burn = make_burn_statmod(
        mod_id="hotlink_heavy_burn",
        duration=6.0,
        total_dmg=burn_heavy_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Heavy",
        callout_text="烈焰火海",
        pua_icon="\uE517",
    )
    mods.update(m_heavy_burn)
    appears.update(a_heavy_burn)

    # 被动: 对手燃烧时近战额外造成 25% 伤害 (ID: 3604)
    m_melee_boost, a_melee_boost = make_attack_boost_statmod(
        mod_id="hotlink_burn_melee_boost",
        duration=4.0,
        attack_bonus=0.25,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy;opp.status=dmg_burn",
        callout_text="炙热猛攻",
        pua_icon="\uE412",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_melee_boost)
    appears.update(a_melee_boost)

    # 3. 觉醒技: 生命低于 50% 获得 6 秒不可阻挡与近战叠层 (ID: 3605)
    m_sig_unstop, a_sig_unstop = make_unstoppable_statmod(
        mod_id="hotlink_sig_unstoppable",
        duration=6.0,
        trigger="onHealthThreshold",
        trigger_scope="health<=0.50",
        callout_text="熔岩霸体",
        pua_icon="\uE915",
    )
    mods.update(m_sig_unstop)
    appears.update(a_sig_unstop)

    m_sig_stack, a_sig_stack = make_attack_boost_statmod(
        mod_id="hotlink_sig_melee_stack",
        duration=5.0,
        attack_bonus=0.15,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Light,Medium,Heavy;opp.status=dmg_burn",
        callout_text="熔岩过载",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_sig_stack)
    appears.update(a_sig_stack)

    # 4. SP1 燃烧与近战增益 (ID: 3606)
    burn_sp1_dmg = base_atk * 0.50
    m_sp1_burn, a_sp1_burn = make_burn_statmod(
        mod_id="hotlink_sp1_burn",
        duration=5.0,
        total_dmg=burn_sp1_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="高温喷流",
        pua_icon="\uE41D",
    )
    mods.update(m_sp1_burn)
    appears.update(a_sp1_burn)

    m_sp1_buff, a_sp1_buff = make_attack_boost_statmod(
        mod_id="hotlink_sp1_melee_buff",
        duration=6.0,
        attack_bonus=0.20,
        chance=1.0,
        trigger="onSpecial1Expiry",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_sp1_buff)
    appears.update(a_sp1_buff)

    # 5. SP2 燃烧与眩晕 (ID: 3607)
    burn_sp2_dmg = base_atk * 0.70
    m_sp2_burn, a_sp2_burn = make_burn_statmod(
        mod_id="hotlink_sp2_burn",
        duration=6.0,
        total_dmg=burn_sp2_dmg,
        chance=0.85,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="高温燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_sp2_burn)
    appears.update(a_sp2_burn)

    m_sp2_stun, a_sp2_stun = make_stun_statmod(
        mod_id="hotlink_sp2_stun",
        duration=1.5,
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Special2",
        target="opponent",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_sp2_stun)
    appears.update(a_sp2_stun)

    # 6. SP3 烈焰地狱、护甲增益与不可阻挡 (ID: 3608)
    burn_sp3_dmg = base_atk * 1.00
    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="hotlink_sp3_burn",
        duration=8.0,
        total_dmg=burn_sp3_dmg,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        callout_text="烈焰炼狱",
        pua_icon="\uE41D",
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    m_sp3_armor, a_sp3_armor = make_armor_up_statmod(
        mod_id="hotlink_sp3_armor",
        duration=8.0,
        armor_bonus=0.30,
        chance=1.0,
        trigger="onSpecial3Expiry",
        callout_text="烈焰护甲",
        pua_icon="\uE515",
    )
    mods.update(m_sp3_armor)
    appears.update(a_sp3_armor)

    m_sp3_unstop, a_sp3_unstop = make_unstoppable_statmod(
        mod_id="hotlink_sp3_unstoppable",
        duration=4.0,
        trigger="onSpecial3Expiry",
        callout_text="不可阻挡",
        pua_icon="\uE915",
    )
    mods.update(m_sp3_unstop)
    appears.update(a_sp3_unstop)

    return mods, appears
