#!/usr/bin/env python3
"""
Bot Ability Implementation: 碾碎器 (Grindor ROTF)
=================================================
Bot ID: grindor_cin_rotf
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 护甲增益 / Armor Up] (ID: 3056, pua_icon: 0xe517, category: passive)
   - 官方描述: "当受到攻击时，有8%的概率获得护甲增益，降低受到攻击伤害的41%，持续6秒"
   - 实现方案:
     grindor_hit_armor:
       触发 onPreDamage, 8% 概率获得 6.0 秒护甲增益 buff (减伤 41%),
       作用于 self, 蓝色血条圆环图标 (PUA: 0xe517, Hex: 3B82F6 / 1D4ED8),
       呼出文字: "护甲"。

2. [被动 - 重击燃烧 / Heavy Burn] (ID: 3072, pua_icon: 0xe41d, category: passive)
   - 官方描述: "重击暴击时有100%概率造成燃烧，施加攻击力80%的伤害，持续6秒。"
   - 实现方案:
     grindor_heavy_crit_burn:
       触发 onCrit, level=Heavy, 100% 概率施加 6.0 秒燃烧 debuff (80% base_atk 伤害),
       作用于 opponent, 橙红血条圆环图标 (PUA: 0xe41d, Hex: FF6600 / CC3300),
       呼出文字: "燃烧"。
-----------------------------------------------------------------------------
"""

from ..core import make_armor_up_statmod, make_burn_statmod
from ..registry import register_bot

BOT_ID = "grindor_cin_rotf"


@register_bot(BOT_ID, name_zh="碾碎器", desc="格斗系，拥有受创触发高额护甲增益与重击暴击燃烧")
def build_grindor_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    """根据基准属性生成碾碎器专属能力修饰器。"""
    mods = {}
    appears = {}

    # 1. ID 3056: 受击 8% 概率获得 41% 减伤护甲，持续 6.0s
    m_armor, a_armor = make_armor_up_statmod(
        mod_id="grindor_hit_armor",
        duration=6.0,
        armor_bonus=0.41,
        chance=1.0,                    # 底层由 Native Hook 仲裁 8% 掷骰并弹出 HUD 显示
        trigger="onPreDamage",
        trigger_scope="",
        appr_id="appr_grindor_hit_armor",
        callout_text="护甲",
        show_callout=True,
        pua_icon="\uE517",
        color_hex="2BDAF6",
        gradient_bottom="0284C7",
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_armor)
    appears.update(a_armor)

    # 2. ID 3072: 重击暴击 100% 造成燃烧 (80% 攻击力伤害，持续 6.0s)
    burn_dmg = 0.80 * base_atk
    m_burn, a_burn = make_burn_statmod(
        mod_id="grindor_heavy_crit_burn",
        duration=6.0,
        total_dmg=burn_dmg,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_grindor_heavy_crit_burn",
        callout_text="燃烧",
        pua_icon="\uE41D",
    )
    mods.update(m_burn)
    appears.update(a_burn)

    return mods, appears
