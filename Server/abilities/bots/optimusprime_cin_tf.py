"""
电影擎天柱 (Optimus Prime MV1 / Movie Optimus) 专属技能实现
Bot ID: optimusprime_cin_tf | 派系: 汽车人 (autobot) | 职业: 格斗系 (braw)

官方数据库能力基准 (Server/tftf_database.db character_abilities):
1. [1793029719669] 被动 护甲增益: 格挡进入 100% 得 -16.5% 护甲增益，持续 7 秒。
2. [1793029719670] 被动 近战增益: 所有攻击 10% 概率获 +60% 近战伤害增益 4 秒（最大 1 层，再获刷新）。
3. [1793029719671] 被动 意志力: 流血时造成所有伤害的 35% 转为自身生命；身上最多 1 层流血，超出的流血当场净化并转化为 +10% 最大能量。
4. [1793029719659] 觉醒 我会带上你们！: 生命 < 20% 时获 1 层 90% 护甲增益 + 3 层 44.4% 近战增益，持续 7 秒，每回合限 1 次（回血超 20% 后再降不再触发）。
5. [1793029719674] SP1 伤害增益: 失去体力越多伤害越高，最高 +150%（50% 体力时 +75%）。
6. [1793029719660] SP1 流血: 60% 概率 4 秒内造成 40% 攻击力流血伤害。
7. [1793029719672] SP2 流血: 前两击每一击 90% 概率 4 秒内造成 40% 攻击力流血伤害。
8. [1793029719673] SP3 流血: 每一击 60% 概率 4 秒内造成 40% 攻击力流血伤害。
"""

from ..core import (
    AbilityColor,
    make_armor_up_statmod,
    make_attack_boost_statmod,
    make_bleed_statmod,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "optimusprime_cin_tf"


@register_bot(BOT_ID, name_zh="电影擎天柱", desc="格斗系重装领袖，进入格挡获得护甲增益，攻击触发近战增益，意志力流血吸血与净化回能，SP1与SP2高额流血")
def build_optimusprime_cin_tf_abilities(base_hp: float = 29334.0, base_atk: float = 2398.0):
    mods = {}
    appears = {}

    # 1. [被动] 护甲增益 (格挡进入 -> 100% -16.5% 护甲增益 7s)
    m_blk, a_blk = make_armor_up_statmod(
        mod_id="optimusprime_cin_tf_block_armor",
        duration=7.0,
        armor_bonus=0.165,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Block",
        appr_id="appr_optimusprime_cin_tf_block_armor",
        callout_text="护甲增益",
        pua_icon="\uE517",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
    )
    mods.update(m_blk)
    appears.update(a_blk)

    # 2. [被动] 近战增益 (所有攻击 10% 概率 +60% 近战伤害 4s, max 1, 刷新 -> 由 C 单一骰点驱动)
    m_mel, a_mel = make_attack_boost_statmod(
        mod_id="optimusprime_cin_tf_melee_buff",
        duration=4.0,
        attack_bonus=0.60,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_melee_buff",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_mel)
    appears.update(a_mel)

    # 3. [被动] 意志力 + 超层流血即时净化呼出
    appr_purify_id = "appr_optimusprime_cin_tf_purify"
    purify_tc = "10B981"
    purify_gb = "059669"
    validate_color_code(purify_tc, "opt_purify_tc")
    validate_color_code(purify_gb, "opt_purify_gb")
    appears[appr_purify_id] = {
        "id": appr_purify_id,
        "a": "净化",
        "s": "",
        "l": "",
        "ss": "",
        "t": "\uE942",
        "f": "",
        "st": "净化",
        "ps": "意志力",
        "pl": "净化流血转能量",
        "tc": purify_tc,
        "gt": purify_tc,
        "gb": purify_gb,
    }
    validate_appear(appears[appr_purify_id])
    mods["optimusprime_cin_tf_purify"] = {
        "id": "optimusprime_cin_tf_purify",
        "t": "combat",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.5,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_gain",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_purify_id],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mods["optimusprime_cin_tf_purify"])

    # 4. [觉醒] 我会带上你们！(HP < 20% 一次性触发: 1层90%护甲 7s + 3层44.4%近战 7s)
    m_sig_arm, a_sig_arm = make_armor_up_statmod(
        mod_id="optimusprime_cin_tf_sig_armor",
        duration=7.0,
        armor_bonus=0.90,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_sig_armor",
        callout_text="护甲增益",
        pua_icon="\uE517",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_sig_arm)
    appears.update(a_sig_arm)

    m_sig_mel, a_sig_mel = make_attack_boost_statmod(
        mod_id="optimusprime_cin_tf_sig_melee",
        duration=7.0,
        attack_bonus=0.444,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_sig_melee",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_sig_mel)
    appears.update(a_sig_mel)

    # 5. [SP1 伤害增益] 指示器 + C 层按已损生命动态增伤 (最高 +150%)
    m_sp1_dmg, a_sp1_dmg = make_attack_boost_statmod(
        mod_id="optimusprime_cin_tf_sp1_dmg_boost",
        duration=5.0,
        attack_bonus=0.0,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_sp1_dmg_boost",
        callout_text="伤害增益",
        pua_icon="\uE406",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_sp1_dmg)
    appears.update(a_sp1_dmg)

    # 6. [SP1 / SP2 / SP3 流血] 均由 C 依据命中/分段状态精确派发
    bleed_total = 0.40 * base_atk
    m_sp1_bld, a_sp1_bld = make_bleed_statmod(
        mod_id="optimusprime_cin_tf_sp1_bleed",
        duration=4.0,
        total_dmg=bleed_total,
        chance=0.60,
        trigger="",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_sp1_bleed",
        callout_text="流血",
        stackable=True,
        buff_id="dmg_bleed",
        target_actor="opponent",
        pua_icon="\uE401",
    )
    mods.update(m_sp1_bld)
    appears.update(a_sp1_bld)

    m_sp2_bld, a_sp2_bld = make_bleed_statmod(
        mod_id="optimusprime_cin_tf_sp2_bleed",
        duration=4.0,
        total_dmg=bleed_total,
        chance=0.90,
        trigger="",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_sp2_bleed",
        callout_text="流血",
        stackable=True,
        buff_id="dmg_bleed",
        target_actor="opponent",
        pua_icon="\uE401",
    )
    mods.update(m_sp2_bld)
    appears.update(a_sp2_bld)

    m_sp3_bld, a_sp3_bld = make_bleed_statmod(
        mod_id="optimusprime_cin_tf_sp3_bleed",
        duration=4.0,
        total_dmg=bleed_total,
        chance=0.60,
        trigger="",
        trigger_scope="",
        appr_id="appr_optimusprime_cin_tf_sp3_bleed",
        callout_text="流血",
        stackable=True,
        buff_id="dmg_bleed",
        target_actor="opponent",
        pua_icon="\uE401",
    )
    mods.update(m_sp3_bld)
    appears.update(a_sp3_bld)

    return mods, appears
