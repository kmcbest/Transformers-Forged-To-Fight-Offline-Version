"""
碾碎器 (Grindor ROTF) 专属技能实现
Bot ID: grindor_cin_rotf | 派系: 霸天虎 (decepticon) | 职业: 格斗系 (braw)

官方数据库能力基准 (Server/tftf_database.db character_abilities):
1. [1793029719291] 被动 护甲增益: 受击时 8% 概率获护甲增益，减伤 41%，持续 6 秒。
2. [1793029719292] 被动 暴击率减益: 受击时 11% 概率造成 1 层暴击率减益(-40%，持续 8 秒)；每层降低对手 15% 格挡精通。
3. [1793029719293] 被动 天然护甲: +17% 永久护甲增益，无图标，不可被破甲移除（C 层常驻减伤）。
4. [1793029719294] 觉醒 贯穿: 所有近战攻击（含 SP1/SP2/SP3 第 1 击）伤害提升 = 110% * 敌方能量百分比（无图标）。
5. [1793029719301] 被动 燃烧: 重击若暴击，100% 造成 6 秒 80% 攻击燃烧。
6. [1793029719305/306] SP1: 施加 1 层 -40% 暴击率减益（8 秒）；35% 概率锁定对手 SP2（6 秒）；75% 概率锁定对手 SP3（6 秒）。
7. [1793029719295/307] SP2: 依据对手当前能量最高 +40% 额外伤害；50% 概率锁定对手 SP3（6 秒）。
8. [1793029719308/309/310] SP3:
   - 100% 锁定对手 SP2 与 SP3（10 秒，能量条对应 2/3 号格显示白色小锁并禁用）
   - 100% 施加 1 层永久 -16% 暴击率减益（可叠加，同样降低 15% 格挡精通）
   - 最后一击暴击率 +50%，若暴击 100% 施加 6 秒 80% 攻击燃烧。
"""

from ..core import (
    AbilityColor,
    make_armor_up_statmod,
    make_burn_statmod,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "grindor_cin_rotf"


def _make_crit_debuff(mod_id: str, crit_delta: float, duration: float, max_stacks: int):
    tc = AbilityColor.RED_DEBUFF_TC
    gb = AbilityColor.RED_DEBUFF_GB
    validate_color_code(tc, f"{mod_id}_tc")
    validate_color_code(gb, f"{mod_id}_gb")
    appr_id = f"appr_{mod_id}"
    appr = {
        "id": appr_id,
        "a": "暴击率减益",
        "s": "",
        "l": "",
        "ss": "",
        "t": "\uE912",
        "f": "",
        "st": "暴击率减益",
        "ps": "暴击率减益",
        "pl": "暴击率与格挡精通降低",
        "tc": tc,
        "gt": tc,
        "gb": gb,
    }
    mod = {
        "id": mod_id,
        "t": "crit_rate",
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": float(crit_delta),
        "d": float(duration),
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": max_stacks,
        "g": "crit_rate_debuff",
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


def _make_disable_sp_mod(mod_id: str, sp_tier: int, duration: float, show_callout: bool = True):
    tc = AbilityColor.RED_DEBUFF_TC
    gb = AbilityColor.RED_DEBUFF_GB
    validate_color_code(tc, f"{mod_id}_tc")
    validate_color_code(gb, f"{mod_id}_gb")
    appr_id = f"appr_{mod_id}"
    sp_type = f"disable_sp{sp_tier}"
    appr = {
        "id": appr_id,
        "a": "战术封锁",
        "s": "",
        "l": "",
        "ss": "",
        "t": "\uE419",
        "f": "",
        "st": "战术封锁" if show_callout else "",
        "ps": "战术封锁",
        "pl": "特殊技被锁定",
        "tc": tc,
        "gt": tc,
        "gb": gb,
    }
    mod = {
        "id": mod_id,
        "t": sp_type,
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": float(duration),
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": sp_type,
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


@register_bot(BOT_ID, name_zh="碾碎器", desc="格斗系巨霸，受击触发护甲/暴击率减益、17%天然护甲、贯穿与SP1/SP2/SP3战术封锁")
def build_grindor_abilities(base_hp: float = 30000.0, base_atk: float = 3000.0):
    mods = {}
    appears = {}

    # 1. [被动] 受击 8% 得护甲增益 (-41%, 6s)
    m_arm, a_arm = make_armor_up_statmod(
        mod_id="grindor_hit_armor",
        duration=6.0,
        armor_bonus=0.41,
        chance=0.08,
        trigger="",
        trigger_scope="",
        appr_id="appr_grindor_hit_armor",
        callout_text="护甲增益",
        pua_icon="\uE517",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        stackable=True,
        max_stacks=3,
    )
    mods.update(m_arm)
    appears.update(a_arm)

    # 2. [被动 / SP1 / SP3] 暴击率减益 (-40% 8s; -16% 永久)
    m_c_pas, a_c_pas = _make_crit_debuff("grindor_struck_crit_debuff", -0.40, 8.0, 5)
    mods.update(m_c_pas)
    appears.update(a_c_pas)

    m_c_sp1, a_c_sp1 = _make_crit_debuff("grindor_sp1_crit_debuff", -0.40, 8.0, 5)
    mods.update(m_c_sp1)
    appears.update(a_c_sp1)

    m_c_sp3, a_c_sp3 = _make_crit_debuff("grindor_sp3_crit_debuff", -0.16, -1.0, 5)
    mods.update(m_c_sp3)
    appears.update(a_c_sp3)

    # 3. [被动 重击 / SP3] 暴击燃烧 (80% ATK, 6s)
    burn_total = 0.80 * base_atk
    m_h_burn, a_h_burn = make_burn_statmod(
        mod_id="grindor_heavy_crit_burn",
        duration=6.0,
        total_dmg=burn_total,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grindor_heavy_crit_burn",
        callout_text="燃烧",
        stackable=True,
        max_stacks=10,
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_h_burn)
    appears.update(a_h_burn)

    m_sp3_burn, a_sp3_burn = make_burn_statmod(
        mod_id="grindor_sp3_crit_burn",
        duration=6.0,
        total_dmg=burn_total,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_grindor_sp3_crit_burn",
        callout_text="燃烧",
        stackable=True,
        max_stacks=10,
        pua_icon="\uE41D",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_burn)
    appears.update(a_sp3_burn)

    # 4. [SP1 / SP2 / SP3 战术封锁] 挂载 disable_sp2 / disable_sp3 驱动原生能量条白锁渲染
    m_sp1_l2, a_sp1_l2 = _make_disable_sp_mod("grindor_sp1_disable_sp2", 2, 6.0)
    mods.update(m_sp1_l2)
    appears.update(a_sp1_l2)

    m_sp1_l3, a_sp1_l3 = _make_disable_sp_mod("grindor_sp1_disable_sp3", 3, 6.0)
    mods.update(m_sp1_l3)
    appears.update(a_sp1_l3)

    m_sp2_l3, a_sp2_l3 = _make_disable_sp_mod("grindor_sp2_disable_sp3", 3, 6.0)
    mods.update(m_sp2_l3)
    appears.update(a_sp2_l3)

    m_sp3_l2, a_sp3_l2 = _make_disable_sp_mod("grindor_sp3_disable_sp2", 2, 10.0)
    mods.update(m_sp3_l2)
    appears.update(a_sp3_l2)

    return mods, appears
