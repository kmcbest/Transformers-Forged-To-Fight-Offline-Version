#!/usr/bin/env python3
"""
Bot Ability Implementation: 通天晓 (Ultra Magnus)
=================================================
Bot ID: ultramagnus_gs_leader
阵营: 汽车人 (Autobot) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [SP1 - 破甲 / Armor Break] (ID: 2865, pua_icon: 0xe516, category: sp1)
   - 官方描述: "移除对方身上所有护甲增益，并按护甲层数施加16.2%的破甲（对方身上如果没有护甲增益，也会施加一层破甲），持续10秒。"
   - 实现方案:
     ultramagnus_sp1_armor_break:
       触发 onHit, level=Special1, 100% 概率施加 10.0 秒破甲 debuff (+16.2% 易伤),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe516, Hex: EF4444 / B91C1C),
       呼出文字: "破甲"。

2. [SP2 - 破甲 / Armor Break] (ID: 2880, pua_icon: 0xe516, category: sp2)
   - 官方描述: "第一击移除对方身上所有护甲增益，并按护甲增益层数施加16.2%的破甲，持续10秒。"
   - 实现方案:
     ultramagnus_sp2_armor_break:
       触发 onHit, level=Special2, 100% 概率施加 10.0 秒破甲 debuff (+16.2% 易伤),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe516, Hex: EF4444 / B91C1C),
       呼出文字: "破甲"。

3. [SP3 - 破甲 / Armor Break] (ID: 2881, pua_icon: 0xe516, category: sp3)
   - 官方描述: "第一击移除对方身上所有护甲增益，并按护甲增益层数施加16.2%的破甲，持续10秒。"
   - 实现方案:
     ultramagnus_sp3_armor_break:
       触发 onHit, level=Special3, 100% 概率施加 10.0 秒破甲 debuff (+16.2% 易伤),
       作用于 opponent, 红色血条圆环图标 (PUA: 0xe516, Hex: EF4444 / B91C1C),
       呼出文字: "破甲"。

4. [被动 - 重击燃烧 / Heavy Burn] (ID: 2874, pua_icon: 0xe41d, category: passive)
   - 官方描述: "重击命中时有65%几率造成燃烧，施加攻击力80%的伤害，持续12秒。"
   - 实现方案:
     ultramagnus_heavy_burn:
       触发 onHit, level=Heavy, 65% 概率施加 12.0 秒燃烧 debuff (80% base_atk 伤害),
       作用于 opponent, 橙红血条圆环图标 (PUA: 0xe41d, Hex: FF6600 / CC3300),
       呼出文字: "燃烧"。

5. [SP2 - 燃烧 / Burn] (ID: 2875, pua_icon: 0xe41d, category: sp2)
   - 官方描述: "最后一击有65%几率造成燃烧，施加攻击力80%的伤害，持续12秒。"
   - 实现方案:
     ultramagnus_sp2_burn:
       触发 onHit, level=Special2, 65% 概率施加 12.0 秒燃烧 debuff (80% base_atk 伤害),
       作用于 opponent, 橙红血条圆环图标 (PUA: 0xe41d, Hex: FF6600 / CC3300),
       呼出文字: "燃烧"。

6. [SP3 - 燃烧 / Burn] (ID: 2876, pua_icon: 0xe41d, category: sp3)
   - 官方描述: "最后一击有65%几率造成燃烧，施加攻击力80%的伤害，持续12秒。"
   - 实现方案:
     ultramagnus_sp3_burn:
       触发 onHit, level=Special3, 65% 概率施加 12.0 秒燃烧 debuff (80% base_atk 伤害),
       作用于 opponent, 橙红血条圆环图标 (PUA: 0xe41d, Hex: FF6600 / CC3300),
       呼出文字: "燃烧"。
-----------------------------------------------------------------------------
"""

from ..core import make_armor_break_statmod, make_burn_statmod
from ..registry import register_bot

BOT_ID = "ultramagnus_gs_leader"


@register_bot(BOT_ID, name_zh="通天晓", desc="战术系，拥有全段SP碎甲破甲、重击与SP强力燃烧")
def build_ultramagnus_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    """根据基准属性生成通天晓专属能力修饰器。"""
    mods = {}
    appears = {}

    # 1. ID 2865: SP1 命中施加 16.2% 破甲，持续 10.0s
    m_sp1_break, a_sp1_break = make_armor_break_statmod(
        mod_id="ultramagnus_sp1_armor_break",
        duration=10.0,
        break_amount=0.162,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_ultramagnus_sp1_armor_break",
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

    # 2. ID 2880: SP2 第一击槌击 (hit 0) 施加 16.2% 破甲，持续 10.0s
    m_sp2_break, a_sp2_break = make_armor_break_statmod(
        mod_id="ultramagnus_sp2_armor_break",
        duration=10.0,
        break_amount=0.162,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2;index=0",
        appr_id="appr_ultramagnus_sp2_armor_break",
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

    # 3. ID 2881: SP3 第一击槌击 (hit 0) 施加 16.2% 破甲，持续 10.0s
    m_sp3_break, a_sp3_break = make_armor_break_statmod(
        mod_id="ultramagnus_sp3_armor_break",
        duration=10.0,
        break_amount=0.162,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3;index=0",
        appr_id="appr_ultramagnus_sp3_armor_break",
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

    # 4. ID 2874: 重击命中 65% 几率燃烧 (80% 攻击力伤害，持续 12s)
    burn_dmg = 0.80 * base_atk
    m_h_burn, a_h_burn = make_burn_statmod(
        mod_id="ultramagnus_heavy_burn",
        duration=12.0,
        total_dmg=burn_dmg,
        chance=1.0,                    # 底层由 Native Hook 仲裁 65% 掷骰并弹出 HUD 显示
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_ultramagnus_heavy_burn",
        callout_text="燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_h_burn)
    appears.update(a_h_burn)

    # 5. ID 2875: SP2 第二下 (最后一下) 导弹命中 65% 几率燃烧 (80% 攻击力伤害，持续 12s)
    m_sp2_burn, a_sp2_burn = make_burn_statmod(
        mod_id="ultramagnus_sp2_burn",
        duration=12.0,
        total_dmg=burn_dmg,
        chance=1.0,                    # 底层由 Native Hook 仲裁 65% 掷骰并弹出 HUD 显示
        trigger="onHit",
        trigger_scope="level=Special2;dmgFlags=LastHit",
        appr_id="appr_ultramagnus_sp2_burn",
        callout_text="燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_sp2_burn)
    appears.update(a_sp2_burn)

    # 6. ID 2876: SP3 后面几下导弹命中 65% 几率燃烧 (80% 攻击力伤害，持续 12s)
    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="ultramagnus_sp3_burn",
        duration=12.0,
        total_dmg=burn_dmg,
        chance=1.0,                    # 底层由 Native Hook 仲裁 65% 掷骰并弹出 HUD 显示
        trigger="onHit",
        trigger_scope="level=Special3;index=1,2,3,4,5",
        appr_id="appr_ultramagnus_sp3_burn",
        callout_text="燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    return mods, appears
