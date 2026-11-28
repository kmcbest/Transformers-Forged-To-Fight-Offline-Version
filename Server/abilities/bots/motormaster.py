"""
汽车大师 (Motormaster G1 / Voyager 2015) 专属技能实现
Bot ID: motormaster_gs_voyager2015 | 派系: 霸天虎 (decepticon) | 职业: 格斗系 (braw)

官方数据库能力基准 (Server/tftf_database.db character_abilities):
1. [1793029719577] 被动 前冲不可阻挡: 远距前冲时进入不可阻挡状态（保留既有稳定验证机制）。
2. [1793029719578] 被动 重击冲压: 重击撞击对手时随机造成三选一减益（均持续 6 秒）：
   - 21.6% 攻击减益
   - 29.7% 破甲减益
   - 24.3% 能量功率减益
3. [1793029719579] 觉醒 公路之王: 每损失最大生命值的 20%，获得 1 层 +60% 近战增益（最大 4 层，无倒计时）。
4. [1793029719589] SP1 能量燃烧: 即时扣除对方最大能量的 2%。
5. [1793029719580] SP2 不可阻挡: 激活时获得 4.5 秒不可阻挡增益。
6. [1793029719581/590] SP3: 最后一击伤害增加 150%，并对自身造成攻击力 90% 反噬伤害（最低保留 1 点生命），
   且随机施加 6 层冲压减益（均持续 6 秒：21.6% 攻击 / 29.7% 破甲 / 24.3% 能量功率）。
"""

from ..core import (
    AbilityColor,
    make_unstoppable_statmod,
    make_attack_boost_statmod,
    make_armor_break_statmod,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "motormaster_gs_voyager2015"


def _make_ram_atk_debuff(mod_id: str, max_stacks: int):
    tc = AbilityColor.RED_DEBUFF_TC
    gb = AbilityColor.RED_DEBUFF_GB
    validate_color_code(tc, f"{mod_id}_tc")
    validate_color_code(gb, f"{mod_id}_gb")
    appr_id = f"appr_{mod_id}"
    appr = {
        "id": appr_id,
        "a": "攻击减益",
        "s": "",
        "l": "",
        "ss": "",
        "t": "\uE916",
        "f": "",
        "st": "攻击减益",
        "ps": "攻击减益",
        "pl": "攻击评级降低",
        "tc": tc,
        "gt": tc,
        "gb": gb,
    }
    mod = {
        "id": mod_id,
        "t": "attack_debuff",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.216,
        "d": 6.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": max_stacks,
        "g": "attack_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr)
    validate_statmod(mod)
    return {mod_id: mod}, {appr_id: appr}


def _make_ram_power_debuff(mod_id: str, max_stacks: int):
    tc = AbilityColor.RED_DEBUFF_TC
    gb = AbilityColor.RED_DEBUFF_GB
    validate_color_code(tc, f"{mod_id}_tc")
    validate_color_code(gb, f"{mod_id}_gb")
    appr_id = f"appr_{mod_id}"
    appr = {
        "id": appr_id,
        "a": "能量功率减益",
        "s": "",
        "l": "",
        "ss": "",
        "t": "\uE607",
        "f": "",
        "st": "能量功率减益",
        "ps": "能量功率减益",
        "pl": "能量获取功率降低",
        "tc": tc,
        "gt": tc,
        "gb": gb,
    }
    mod = {
        "id": mod_id,
        "t": "power_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": -0.243,
        "d": 6.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": max_stacks,
        "g": "power_rate_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_appear(appr)
    validate_statmod(mod)
    return {mod_id: mod}, {appr_id: appr}


@register_bot(BOT_ID, name_zh="汽车大师", desc="格斗系，前冲与SP2不可阻挡霸体、重击冲压随机三重削弱、公路之王残血近战爆发、SP1烧能与SP3舍身轰击")
def build_motormaster_abilities(base_hp: float = 34894.0, base_atk: float = 2629.0):
    mods = {}
    appears = {}

    # 1. [被动] 前冲不可阻挡
    m_dash, a_dash = make_unstoppable_statmod(
        mod_id="motormaster_dash_unstoppable",
        duration=0.55,
        trigger="",
        trigger_scope="",
        appr_id="appr_motormaster_dash_unstoppable",
        callout_text="不可阻挡",
        play_vfx=True,
        pua_icon="\uE915",
    )
    mods.update(m_dash)
    appears.update(a_dash)

    # 2. [SP2] 大师工艺：激活获得 4.5s 不可阻挡
    m_sp2, a_sp2 = make_unstoppable_statmod(
        mod_id="motormaster_sp2_unstoppable",
        duration=4.5,
        trigger="",
        trigger_scope="",
        appr_id="appr_motormaster_sp2_unstoppable",
        callout_text="不可阻挡",
        play_vfx=True,
        pua_icon="\uE915",
    )
    mods.update(m_sp2)
    appears.update(a_sp2)

    # 3. [被动] 重击冲压：C 三选一随机施加
    m_h_atk, a_h_atk = _make_ram_atk_debuff("motormaster_heavy_atk_debuff", max_stacks=3)
    mods.update(m_h_atk)
    appears.update(a_h_atk)

    m_h_arm, a_h_arm = make_armor_break_statmod(
        mod_id="motormaster_heavy_armor_break",
        duration=6.0,
        break_amount=0.297,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_motormaster_heavy_armor_break",
        callout_text="破甲",
        pua_icon="\uE516",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_h_arm)
    appears.update(a_h_arm)

    m_h_pwr, a_h_pwr = _make_ram_power_debuff("motormaster_heavy_power_debuff", max_stacks=3)
    mods.update(m_h_pwr)
    appears.update(a_h_pwr)

    # 4. [觉醒] 公路之王：每损失 20% HP 得 1 层 +60% 近战增益 (最大 4 层，永久)
    m_king, a_king = make_attack_boost_statmod(
        mod_id="motormaster_sig_king",
        duration=-1.0,
        attack_bonus=0.60,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_motormaster_sig_king",
        callout_text="近战增益",
        pua_icon="\uE412",
        stackable=True,
        max_stacks=4,
    )
    mods.update(m_king)
    appears.update(a_king)

    # 5. [SP1 离子刀] 能量燃烧：即时扣除对手最大能量的 2%
    validate_color_code(AbilityColor.RED_DEBUFF_TC, "mm_pburn_tc")
    validate_color_code(AbilityColor.RED_DEBUFF_GB, "mm_pburn_gb")
    appears["appr_motormaster_sp1_power_burn"] = {
        "id": "appr_motormaster_sp1_power_burn",
        "a": "能量燃烧",
        "s": "",
        "l": "",
        "ss": "",
        "t": "\uE607",
        "f": "",
        "st": "能量燃烧",
        "ps": "能量燃烧",
        "pl": "能量被扣除",
        "tc": AbilityColor.RED_DEBUFF_TC,
        "gt": AbilityColor.RED_DEBUFF_TC,
        "gb": AbilityColor.RED_DEBUFF_GB,
    }
    validate_appear(appears["appr_motormaster_sp1_power_burn"])
    mods["motormaster_sp1_power_burn"] = {
        "id": "motormaster_sp1_power_burn",
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
        "d": 0.5,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "power_leak",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_motormaster_sp1_power_burn"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mods["motormaster_sp1_power_burn"])

    # 6. [SP3 冲压全开] 随机施加 6 层冲压减益 (每层均持续 6s)
    m_sp3_atk, a_sp3_atk = _make_ram_atk_debuff("motormaster_sp3_atk_debuff", max_stacks=6)
    mods.update(m_sp3_atk)
    appears.update(a_sp3_atk)

    m_sp3_arm, a_sp3_arm = make_armor_break_statmod(
        mod_id="motormaster_sp3_ram_armor",
        duration=6.0,
        break_amount=0.297,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_motormaster_sp3_ram_armor",
        callout_text="破甲",
        pua_icon="\uE516",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
        stackable=True,
        max_stacks=6,
    )
    mods.update(m_sp3_arm)
    appears.update(a_sp3_arm)

    m_sp3_pwr, a_sp3_pwr = _make_ram_power_debuff("motormaster_sp3_power_debuff", max_stacks=6)
    mods.update(m_sp3_pwr)
    appears.update(a_sp3_pwr)

    return mods, appears
