#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影铁皮 (Ironhide ROTF)
====================================================
Bot ID: ironhide_cin_rotf
阵营: 汽车人 (Autobot) | 职业: 爆破系 (Demolition)

【官方技能与二层收口实现说明】：
1. [passive] 暴击伤害 (Crit Damage, 0xe906):
   - 铁皮受到攻击时：有 12% 的概率获得暴击伤害增益，增加 140% 的暴击伤害，持续 8 秒。
   - StatMod: ironhide_struck_crit_dmg (tr=[], 由 skill_ironhide.c on_hit_connected 触发)。
2. [passive] 燃烧 (Burn, 0xe41d):
   - 所有导弹攻击（重击、SP1 的最后一击、SP2 的所有攻击）命中时有 70% 几率造成燃烧，施加攻击力 80% 的伤害，持续 4 秒。
   - 若对手正在燃烧中，则燃烧可以叠加，每层 4 秒，伤害为攻击力的 30%。
   - StatMods: ironhide_missile_burn / ironhide_missile_burn_stack (tr=[], 由 skill_ironhide.c 门控触发)。
3. [passive] 导弹暴击 (Missile Crit, 0xe40d):
   - 所有导弹攻击（重击、SP1 的最后一击、SP2 的所有攻击）+100% 暴击概率。
   - 由 skill_ironhide.c on_crit_chance_mod 按单次命中精准加权 +100% 暴击率；保留 ironhide_missile_crit (tr=[]) 描述条目。
4. [sp1] 眩晕 (Stun, 0xe605):
   - 最后一击有 80% 概率造成眩晕，持续 2.5 秒。
   - StatMod: ironhide_sp1_stun (tr=[], 由 skill_ironhide.c on_hit_connected 末击触发)。
5. [sp2] 暴击伤害 (Crit Damage, 0xe406):
   - 有 76% 的概率获得暴击伤害增益，增加 75% 的暴击伤害，持续 4 秒。
   - StatMod: ironhide_s2_crit_dmg (tr=["onSpecial2Activate"])。
6. [sp3] 燃烧 (Burn, 0xe41d):
   - 最后一击有 30% 几率造成燃烧，施加攻击力 100% 的伤害，持续 8 秒。
   - StatMod: ironhide_s3_burn (tr=[], 由 skill_ironhide.c on_hit_connected SP3 末击触发)。
7. [signature] 抹杀 (Obliteration, 0xe406):
   - 特殊技有 50% 几率造成 +600% 暴击伤害（5 星满觉基准），每场战斗可触发一次。
   - StatMod: ironhide_sig_obliteration (tr=[], 由 skill_ironhide.c on_special_state 进出生命周期控制)。
"""

from ..core import (
    AbilityColor,
    make_burn_statmod,
    make_crit_rate_statmod,
    make_crit_damage_statmod,
    make_stun_statmod,
)
from ..registry import register_bot

BOT_ID = "ironhide_cin_rotf"


@register_bot(
    BOT_ID,
    name_zh="电影铁皮",
    desc="爆破系重炮手：重击与SP导弹必暴叠层燃烧、受击暴伤、SP1末击眩晕、SP2暴伤、SP3末击烈焰、觉醒抹杀一击",
)
def build_ironhide_abilities(base_hp: float = 33602.0, base_atk: float = 2531.0):
    mods = {}
    appears = {}

    # 1a. 导弹初次燃烧 (80% ATK, 持续 4 秒) -> C 侧 70% 概率触发 (非燃烧目标)
    m1, a1 = make_burn_statmod(
        mod_id="ironhide_missile_burn",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1)
    appears.update(a1)

    # 1b. 导弹叠层燃烧 (30% ATK, 持续 4 秒) -> C 侧 70% 概率触发 (燃烧中目标)
    m1_stack, a1_stack = make_burn_statmod(
        mod_id="ironhide_missile_burn_stack",
        duration=4.0,
        total_dmg=float(round(base_atk * 0.30)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m1_stack)
    appears.update(a1_stack)

    # 2. 导弹暴击率条目 (运行时由 skill_ironhide.c on_crit_chance_mod 精准判定 +100% 暴击)
    m2, a2 = make_crit_rate_statmod(
        mod_id="ironhide_missile_crit",
        duration=0.8,
        crit_bonus=1.00,
        chance=1.0,
        trigger="",
        trigger_scope="",
        callout_text="导弹暴击",
        pua_icon="\uE40D",
    )
    mods.update(m2)
    appears.update(a2)

    # 3. [passive] 受击暴击伤害 (+140% 暴击伤害, 持续 8 秒, 受击时 C 侧 12% 触发)
    m_struck, a_struck = make_crit_damage_statmod(
        mod_id="ironhide_struck_crit_dmg",
        duration=8.0,
        crit_dmg_bonus=1.40,
        chance=1.0,
        trigger="",
        callout_text="暴击伤害",
        pua_icon="\uE906",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m_struck)
    appears.update(a_struck)

    # 4. [sp1] 感觉走运 - 末击眩晕 (2.5 秒, SP1 末击命中时 C 侧 80% 触发)
    m_sp1_stun, a_sp1_stun = make_stun_statmod(
        mod_id="ironhide_sp1_stun",
        duration=2.5,
        chance=1.0,
        trigger="",
        appr_id="appr_ironhide_sp1_stun",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_sp1_stun)
    appears.update(a_sp1_stun)

    # 5. [sp2] 打破僵持 - 暴击伤害增益 (+75% 暴击伤害, 持续 4 秒, 76% 几率)
    m3, a3 = make_crit_damage_statmod(
        mod_id="ironhide_s2_crit_dmg",
        duration=4.0,
        crit_dmg_bonus=0.75,
        chance=0.76,
        trigger="onSpecial2Activate",
        callout_text="暴击伤害",
        pua_icon="\uE406",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m3)
    appears.update(a3)

    # 6. [sp3] 全金属军械库 - 末击燃烧 (100% ATK, 持续 8 秒, SP3 末击 C 侧 30% 触发)
    m4, a4 = make_burn_statmod(
        mod_id="ironhide_s3_burn",
        duration=8.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        callout_text="燃烧",
        stackable=True,
        pua_icon="\uE41D",
    )
    mods.update(m4)
    appears.update(a4)

    # 7. [signature] 抹杀 Obliteration (+600% 暴击伤害, 特殊技 50% 触发, 每局一次)
    m_sig, a_sig = make_crit_damage_statmod(
        mod_id="ironhide_sig_obliteration",
        duration=8.0,
        crit_dmg_bonus=6.00,
        chance=1.0,
        trigger="",
        callout_text="抹杀",
        pua_icon="\uE406",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m_sig)
    appears.update(a_sig)

    return mods, appears
