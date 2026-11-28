"""
钢锁 (Grimlock G1 / MP-08) 专属技能实现
Bot ID: grimlock_gs_mp08 | 派系: 汽车人 (autobot) | 职业: 格斗系 (braw)

官方数据库能力基准 (Server/tftf_database.db character_abilities):
1. [1793029719275] 被动 近战增益: 受击 14% 概率获 1 层近战增益，增加近战伤害 16%，持续 5 秒，可叠加。
2. [1793029719276] 觉醒 恐龙之怒: 受到带倒计时伤害减益(流血/震击/燃烧/酸液等)后 1 秒净化该减益，并 30% 概率获 1 层 +30% 近战增益，持续 5 秒，可叠加（即时/爆头/驱散震击/黑暗燃烧除外）。
3. [1793029719282] 被动 不可阻挡: 重击全程进入不可阻挡状态，并刷新身上所有近战增益的倒计时。
4. [1793029719281] 被动 燃烧: 重击命中 70% 概率造成燃烧，2 秒 50% 攻击伤害。
5. [1793029719283/284] SP1: 100% 获 1 层 +12% 近战增益（5 秒）；最后一击（第2击喷火）100% 造成燃烧，4 秒 100% 攻击伤害。
6. [1793029719285] SP2: 100% 获 1 层 +18% 近战增益（5 秒）。
7. [1793029719286/287] SP3: 100% 获 1 层 +30% 近战增益（5 秒）；100% 造成燃烧，7 秒 150% 攻击伤害。
"""

from ..core import (
    AbilityColor,
    make_attack_boost_statmod,
    make_burn_statmod,
    make_unstoppable_statmod,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "grimlock_gs_mp08"


@register_bot(BOT_ID, name_zh="钢锁", desc="格斗系暴龙领袖，受创累加近战增益，恐龙之怒净化DOT减益，重击霸体与暴烈喷火燃烧")
def build_grimlock_abilities(base_hp: float = 34000.0, base_atk: float = 2100.0):
    mods = {}
    appears = {}

    # 1. [被动] 受击 14% 得 1 层 +16% 近战增益 (5s, 可叠加 -> 由 C 驱动)
    m_hit_mel, a_hit_mel = make_attack_boost_statmod(
        mod_id="grimlock_takehit_melee_buff",
        duration=5.0,
        attack_bonus=0.16,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_takehit_melee_buff",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_hit_mel)
    appears.update(a_hit_mel)

    # 2. [觉醒] 恐龙之怒 (+30% 近战增益 5s, 可叠加; C 1秒后净化并30%触发)
    m_sig_mel, a_sig_mel = make_attack_boost_statmod(
        mod_id="grimlock_sig_melee_buff",
        duration=5.0,
        attack_bonus=0.30,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_sig_melee_buff",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=10,
    )
    mods.update(m_sig_mel)
    appears.update(a_sig_mel)

    # 恐龙之怒净化呼出提示 (短暂呼出指示)
    m_rage, a_rage = make_attack_boost_statmod(
        mod_id="grimlock_dino_rage",
        duration=1.5,
        attack_bonus=0.0,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_dino_rage",
        callout_text="恐龙之怒",
        pua_icon="\uE412",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_rage)
    appears.update(a_rage)

    # 3. [重击] 全程不可阻挡 + 刷新所有近战增益倒计时 + 70% 2s 50% 燃烧
    m_h_unstop, a_h_unstop = make_unstoppable_statmod(
        mod_id="grimlock_heavy_unstoppable",
        duration=2.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_heavy_unstoppable",
        callout_text="不可阻挡",
        play_vfx=True,
        pua_icon="\uE915",
    )
    mods.update(m_h_unstop)
    appears.update(a_h_unstop)

    m_h_burn, a_h_burn = make_burn_statmod(
        mod_id="grimlock_heavy_burn",
        duration=2.0,
        total_dmg=0.50 * base_atk,
        chance=0.70,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_heavy_burn",
        callout_text="燃烧",
        stackable=True,
        max_stacks=10,
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_h_burn)
    appears.update(a_h_burn)

    # 4. [SP1 恐龙战队] +12% 近战增益 5s; 末击 100% 4s 100% ATK 燃烧
    m_sp1_mel, a_sp1_mel = make_attack_boost_statmod(
        mod_id="grimlock_sp1_melee_buff",
        duration=5.0,
        attack_bonus=0.12,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_sp1_melee_buff",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=5,
    )
    mods.update(m_sp1_mel)
    appears.update(a_sp1_mel)

    m_sp1_burn, a_sp1_burn = make_burn_statmod(
        mod_id="grimlock_sp1_burn",
        duration=4.0,
        total_dmg=1.00 * base_atk,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_sp1_burn",
        callout_text="燃烧",
        stackable=True,
        max_stacks=10,
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp1_burn)
    appears.update(a_sp1_burn)

    # 5. [SP2 震颤] +18% 近战增益 5s
    m_sp2_mel, a_sp2_mel = make_attack_boost_statmod(
        mod_id="grimlock_sp2_melee_buff",
        duration=5.0,
        attack_bonus=0.18,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_sp2_melee_buff",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=5,
    )
    mods.update(m_sp2_mel)
    appears.update(a_sp2_mel)

    # 6. [SP3 国王] +30% 近战增益 5s; 100% 7s 150% ATK 燃烧
    m_sp3_mel, a_sp3_mel = make_attack_boost_statmod(
        mod_id="grimlock_sp3_melee_buff",
        duration=5.0,
        attack_bonus=0.30,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_sp3_melee_buff",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=5,
    )
    mods.update(m_sp3_mel)
    appears.update(a_sp3_mel)

    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="grimlock_sp3_burn",
        duration=7.0,
        total_dmg=1.50 * base_atk,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grimlock_sp3_burn",
        callout_text="燃烧",
        stackable=True,
        max_stacks=10,
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    return mods, appears
