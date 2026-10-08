#!/usr/bin/env python3
"""
Bot Ability Implementation: G1 擎天柱 (G1 Optimus Prime)
======================================================
Bot ID: fte_optimus_gs_t3
阵营: 汽车人 (Autobot) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 护甲增益 / Armor Up] (ID: 2355, pua_icon: 0xe517, category: passive)
   - 官方描述: "当进入格挡姿态时，有100%的概率获得护甲增益，降低受到攻击伤害的16.5%，持续2.5秒。每个小队成员额外提供15%的护甲增益。"
   - 实现方案:
     optimus_block_armor:
       触发 onPlayerStateEnter, state=Block, 100% 概率获得 2.5 秒护甲增益 buff (减伤 16.5%),
       作用于 self, 蓝色血条圆环图标 (PUA: 0xe517, Hex: 3B82F6 / 1D4ED8),
       呼出文字: "护甲"。

2. [SP1 - 破甲 / Armor Break] (ID: 2354, pua_icon: 0xe516, category: sp1)
   - 官方描述: "第二击与第三击92%的概率施加破甲，首先移除对方身上一层护甲增益，并施加20%的破甲减益，持续3.5秒。"
   - 实现方案:
     optimus_sp1_armor_break:
       触发 onHit, level=Special1, 92% 概率对对手施加 3.5 秒破甲 debuff (+20% 易伤),
       底层 ArmorBreak_BuffEffect.OnAdd 自动移除对方 1 层 armor_up 护甲增益,
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe516, Hex: EF4444 / B91C1C),
       呼出文字: "破甲"。

3. [SP1 - 攻击增益 / Attack Buff] (ID: 2360, pua_icon: 0xe406, category: sp1)
   - 官方描述: "获得一个攻击增益，增加20%的攻击力，持续6秒"
   - 实现方案:
     optimus_sp1_atk_buff:
       触发 onSpecial1Activate, 100% 概率获得 6.0 秒攻击增益 (+20% 攻击力),
       作用于 self, 金色血条圆环图标 (PUA: 0xe406, Hex: F59E0B / D97706),
       呼出文字: "攻击加成"。

4. [SP2 - 破甲 / Armor Break] (ID: 2337, pua_icon: 0xe516, category: sp2)
   - 官方描述: "每一击都有92%的概率施加破甲，首先移除对方身上一层护甲增益，并施加35%的破甲减益，持续6秒。"
   - 实现方案:
     optimus_sp2_armor_break:
       触发 onHit, level=Special2, 92% 概率对对手施加 6.0 秒破甲 debuff (+35% 易伤),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe516, Hex: EF4444 / B91C1C),
       呼出文字: "破甲"。

5. [SP3 - 永久破甲 / Permanent Armor Break] (ID: 2359, pua_icon: 0xe516, category: sp3)
   - 官方描述: "每一击都有92%的概率施加破甲，首先移除对方身上一层护甲增益，并施加35%的破甲减益，持续6秒。"
   - 实现方案:
     optimus_sp3_armor_break:
       触发 onHit, level=Special3, 92% 概率对对手施加 6.0 秒破甲 debuff (+35% 易伤),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe516, Hex: EF4444 / B91C1C),
       呼出文字: "破甲"。

6. [觉醒技 - 突破口 / Signature - Exploit Weakness] (ID: 2335, pua_icon: 0xe401, category: signature)
   - 官方描述: "当对手身上有破甲减益时，擎天柱的暴击100%会造成流血，施加攻击力140%的伤害，持续4秒"
   - 实现方案:
     optimus_sig_armor_break_bleed:
       触发 onCrit, trigger_scope="opp.status=armor_break",
       100% 概率对对手施加 4.0 秒流血 debuff (总计 140% base_atk 伤害),
       作用于 opponent, 鲜红血条圆环图标 (PUA: 0xe401, Hex: FF0000 / FF0000),
       呼出文字: "突破口"。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_armor_up_statmod,
    make_armor_break_statmod,
    make_attack_boost_statmod,
    make_bleed_statmod,
)
from ..registry import register_bot

BOT_ID = "fte_optimus_gs_t3"


@register_bot(BOT_ID, name_zh="G1擎天柱", desc="战术系，拥有格挡护甲、多段破甲、攻击增益与破甲暴击流血【突破口】")
def build_optimus_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    """根据基准属性生成 G1 擎天柱专属能力修饰器。"""
    mods = {}
    appears = {}

    # 1. ID 2355: 进入格挡姿态 100% 获得 16.5% 减伤护甲，持续 2.5s
    m_armor, a_armor = make_armor_up_statmod(
        mod_id="optimus_block_armor",
        duration=2.5,
        armor_bonus=0.165,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_optimus_block_armor",
        callout_text="护甲",
        show_callout=True,
        pua_icon="\uE517",
        color_hex="3B82F6",
        gradient_bottom="1D4ED8",
        stackable=True,
        max_stacks=5,
    )
    mods.update(m_armor)
    appears.update(a_armor)

    # 2. ID 2354: SP1 命中 92% 概率施加 20% 破甲，持续 3.5s
    m_sp1_break, a_sp1_break = make_armor_break_statmod(
        mod_id="optimus_sp1_armor_break",
        duration=3.5,
        break_amount=0.20,
        chance=0.92,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_optimus_sp1_armor_break",
        callout_text="破甲",
        show_callout=True,
        pua_icon="\uE516",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sp1_break)
    appears.update(a_sp1_break)

    # 3. ID 2360: SP1 激活 100% 获得 +20% 攻击力增益，持续 6.0s
    m_sp1_atk, a_sp1_atk = make_attack_boost_statmod(
        mod_id="optimus_sp1_atk_buff",
        duration=6.0,
        attack_bonus=0.20,
        chance=1.0,
        trigger="onSpecial1Activate",
        trigger_scope="",
        appr_id="appr_optimus_sp1_atk_buff",
        callout_text="攻击加成",
        show_callout=True,
        pua_icon="\uE406",
        color_hex="F59E0B",
        gradient_bottom="D97706",
        stackable=True,
        max_stacks=5,
    )
    mods.update(m_sp1_atk)
    appears.update(a_sp1_atk)

    # 4. ID 2337: SP2 命中 92% 概率施加 35% 破甲，持续 6.0s
    m_sp2_break, a_sp2_break = make_armor_break_statmod(
        mod_id="optimus_sp2_armor_break",
        duration=6.0,
        break_amount=0.35,
        chance=0.92,
        trigger="onHit",
        trigger_scope="level=Special2",
        appr_id="appr_optimus_sp2_armor_break",
        callout_text="破甲",
        show_callout=True,
        pua_icon="\uE516",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sp2_break)
    appears.update(a_sp2_break)

    # 5. ID 2359: SP3 命中 92% 概率施加 35% 破甲，持续 6.0s
    m_sp3_break, a_sp3_break = make_armor_break_statmod(
        mod_id="optimus_sp3_armor_break",
        duration=6.0,
        break_amount=0.35,
        chance=0.92,
        trigger="onHit",
        trigger_scope="level=Special3",
        appr_id="appr_optimus_sp3_armor_break",
        callout_text="破甲",
        show_callout=True,
        pua_icon="\uE516",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sp3_break)
    appears.update(a_sp3_break)

    # 6. ID 2335: 觉醒技【突破口】对手破甲时暴击 100% 造成 140% 攻击力流血，持续 4.0s
    sig_bleed_dmg = 1.40 * base_atk
    m_sig_bleed, a_sig_bleed = make_bleed_statmod(
        mod_id="optimus_sig_armor_break_bleed",
        duration=4.0,
        total_dmg=sig_bleed_dmg,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="opp.status=armor_break",
        appr_id="appr_optimus_sig_armor_break_bleed",
        callout_text="突破口",
        pua_icon="\uE401",
    )
    mods.update(m_sig_bleed)
    appears.update(a_sig_bleed)

    return mods, appears
