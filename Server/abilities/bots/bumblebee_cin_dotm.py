#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影大黄蜂 (Bumblebee DOTM)
======================================================
Bot ID: bumblebee_cin_dotm
阵营: 汽车人 (Autobot) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 近战校准 / Melee Calibration] (ID: 2421, pua_icon: 0xe509, category: passive)
   - 官方描述: "开局自动获得一个近战规避，无倒计时。25.5%的概率规避对手的近战攻击。
     如果拥有远程规避时被对手近战攻击击中，则出现灰色的近战规避倒计时图标1.5秒，结束后重新获得近战规避。"
   - 实现方案:
     a) bumblebee_cin_dotm_calib_melee: 触发 onStart, 获得常驻近战规避 buff (25.5% 规避几率, d=-1.0)。
     b) bumblebee_cin_dotm_calib_melee_cd: 受敏捷加成缩短16%后为 1.26s 灰色倒计时图标 (t=dotm_calib_melee_cd)，
        与 skill_bumblebee_dotm.c 配合完成切换与绿字“规避”呼出。

2. [被动 - 远程校准 / Ranged Calibration] (ID: 2422, pua_icon: 0xe518, category: passive)
   - 官方描述: "拥有近战规避时被对手远程攻击击中，近战规避消失，出现灰色的远程规避倒计时图标1.5秒，
     结束后获得远程规避，无倒计时，25.5%的概率规避对手的远程攻击。近战规避消失。"
   - 实现方案:
     a) bumblebee_cin_dotm_calib_ranged: 由 C 模块切换后主动施加常驻远程规避 buff (25.5% 规避几率, d=-1.0)。
     b) bumblebee_cin_dotm_calib_ranged_cd: 受敏捷加成缩短16%后为 1.26s 灰色倒计时图标 (t=dotm_calib_ranged_cd)。

3. [被动 - 攻击增益 / Attack Buff] (ID: 2424, pua_icon: 0xe406, category: passive)
   - 官方描述: "每击倒对手一次：获得一个永久攻击增益，攻击力增加13.5%。
     永久增益最多堆叠15层，第16层开始出现倒计时，3秒后消失。"
   - 实现方案:
     a) bumblebee_cin_dotm_knockdown_atk: tr=[] 由 C 模块在非格挡重击/特技击倒对手时主动施加 (+13.5% ATK, d=-1.0, 最多15层)。
     b) bumblebee_cin_dotm_burst_atk: 满15层后击倒对手施加第16+层橙色攻击增益 (+13.5% ATK, d=3.0s, 共享 attack_buff 槽位触发3秒倒计时)。

4. [觉醒 - 敏捷 / Alacrity] (pua_icon: 0xe406, category: signature)
   - 官方描述: "大黄蜂在远程和近战校准模式之间切换时间缩短16%。闪避近战攻击可以获得1层75%的攻击增益，持续5秒。"
   - 实现方案:
     a) 校准切换冷却由 1.5s 缩短 16% -> 1.26s。
     b) bumblebee_cin_dotm_sig_atk: tr=[] 由 C 模块在主动闪避近战攻击时施加 1 层 +75% 攻击增益，
        持续 5.0 秒（不可叠加，最大 1 层，再次触发刷新倒计时）。

5. [SP1 - 速踢 / 破甲 (Armor Break)] (ID: 2426, pua_icon: 0xe516, category: sp1)
   - 官方描述: "每一击都有60%的概率施加破甲，移除对方身上所有护甲增益，并施加35%的破甲减益，持续6秒。"
   - 实现方案:
     bumblebee_cin_dotm_sp1_armor_break: tr=[] 由 C 模块在 SP1 非格挡每段命中时以 60% 概率施加 6 秒 35% 破甲，
     并在施加成功后清除对方身上全部剩余护甲增益。

6. [SP2 - 漏洞射击 / 震击 (Shock)] (ID: 2427, pua_icon: 0xe914, category: sp2)
   - 官方描述: "最后一击施加震击，造成攻击力80%的伤害，持续10秒，对方身上如果有护甲，震击伤害增加150%"
   - 实现方案:
     a) bumblebee_cin_dotm_sp2_shock: tr=[] 非格挡 SP2 最后一击对无护甲目标施加 10 秒 80% ATK 震击。
     b) bumblebee_cin_dotm_sp2_shock_armored: 若对方身上有护甲，震击伤害增加 150% -> 200% ATK (10秒)。

7. [SP3 - 炮弹冲击波 / 震击 (Shock)] (ID: 2436, pua_icon: 0xe914, category: sp3)
   - 官方描述: "最后一击施加震击，造成攻击力80%的伤害，持续10秒，对方身上如果有护甲，震击伤害增加100%"
   - 实现方案:
     a) bumblebee_cin_dotm_sp3_shock: tr=[] SP3 最后一击对无护甲目标施加 10 秒 80% ATK 震击。
     b) bumblebee_cin_dotm_sp3_shock_armored: 若对方身上有护甲，震击伤害增加 100% -> 160% ATK (10秒)。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_attack_boost_statmod,
    make_evade_grant_statmod,
    make_armor_break_statmod,
    make_shock_statmod,
    make_statmod_appearance,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "bumblebee_cin_dotm"


def _make_calib_cd_statmod(mod_id: str, buff_type: str, appr_id: str, callout_text: str, pua_icon: str):
    """构造独立分组的灰色校准切换倒计时 Buff (避免与 evade_melee/evade_ranged 冲突)."""
    appear = make_statmod_appearance(
        appr_id=appr_id,
        callout_text=callout_text,
        pua_icon=pua_icon,
        color=AbilityColor.GRAY_COOLDOWN,
        show_callout=False,
        active_desc=f"{callout_text}中",
    )
    stat_mod = {
        "id": mod_id,
        "t": buff_type,
        "tm": "",
        "tr": [],
        "uit": [],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 1.26,  # 1.5s * (1 - 16% 敏捷觉醒缩短)
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": buff_type,
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_id],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(stat_mod)
    return {mod_id: stat_mod}, {appr_id: appear}


@register_bot(BOT_ID, name_zh="大黄蜂", desc="战术系特工，双模校准规避近战/远程攻击、觉醒敏捷缩减切换并闪避增攻、击倒叠层攻击增益、SP1全清破甲、SP2/3破甲震击")
def build_bumblebee_cin_dotm_abilities(base_hp: float = 28550.0, base_atk: float = 2280.0):
    mods = {}
    appears = {}

    # 1. 击倒对手永久攻击增益 (+13.5% ATK, d=-1.0, 最多15层) (ID: 2424)
    m_kd, a_kd = make_attack_boost_statmod(
        mod_id="bumblebee_cin_dotm_knockdown_atk",
        duration=-1.0,
        attack_bonus=0.135,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_knockdown_atk",
        callout_text="攻击增益",
        show_callout=True,
        pua_icon="\uE406",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=True,
        max_stacks=15,
    )
    mods.update(m_kd)
    appears.update(a_kd)

    # 1b. 第 16+ 层满溢攻击增益 (+13.5% ATK, 3.0秒倒计时, 橙色攻击增益) (ID: 2424b)
    m_burst, a_burst = make_attack_boost_statmod(
        mod_id="bumblebee_cin_dotm_burst_atk",
        duration=3.0,
        attack_bonus=0.135,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_burst_atk",
        callout_text="攻击增益",
        show_callout=True,
        pua_icon="\uE406",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=True,
        max_stacks=15,
    )
    mods.update(m_burst)
    appears.update(a_burst)

    # 1c. 觉醒技【敏捷】: 闪避近战攻击获得 1 层 +75% 攻击增益，持续 5.0 秒 (不可叠加，再次触发刷新)
    m_sig, a_sig = make_attack_boost_statmod(
        mod_id="bumblebee_cin_dotm_sig_atk",
        duration=5.0,
        attack_bonus=0.75,
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_sig_atk",
        callout_text="攻击增益",
        show_callout=True,
        pua_icon="\uE406",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_sig)
    appears.update(a_sig)

    # 2. 近战校准规避 (ID: 2421): 开局自动获得近战规避 (d=-1.0, 25.5% 规避率)
    m_ev_m, a_ev_m = make_evade_grant_statmod(
        mod_id="bumblebee_cin_dotm_calib_melee",
        evade_type="melee",
        grant_chance=1.0,
        evade_chance=0.255,
        duration=0.0,
        trigger="onStart",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_calib_melee",
        callout_text="近战校准",
        show_callout=True,
    )
    mods.update(m_ev_m)
    appears.update(a_ev_m)

    # 2b. 近战校准切换倒计时 (1.26秒灰色近战规避倒计时图标 \uE509)
    m_ev_m_cd, a_ev_m_cd = _make_calib_cd_statmod(
        mod_id="bumblebee_cin_dotm_calib_melee_cd",
        buff_type="dotm_calib_melee_cd",
        appr_id="appr_bumblebee_cin_dotm_calib_melee_cd",
        callout_text="近战校准切换",
        pua_icon="\uE509",
    )
    mods.update(m_ev_m_cd)
    appears.update(a_ev_m_cd)

    # 3. 远程校准规避 (ID: 2422): 切换后由 C 主动施加 (d=-1.0, 25.5% 规避率)
    m_ev_r, a_ev_r = make_evade_grant_statmod(
        mod_id="bumblebee_cin_dotm_calib_ranged",
        evade_type="ranged",
        grant_chance=1.0,
        evade_chance=0.255,
        duration=0.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_calib_ranged",
        callout_text="远程校准",
        show_callout=True,
    )
    mods.update(m_ev_r)
    appears.update(a_ev_r)

    # 3b. 远程校准切换倒计时 (1.26秒灰色远程规避倒计时图标 \uE518)
    m_ev_r_cd, a_ev_r_cd = _make_calib_cd_statmod(
        mod_id="bumblebee_cin_dotm_calib_ranged_cd",
        buff_type="dotm_calib_ranged_cd",
        appr_id="appr_bumblebee_cin_dotm_calib_ranged_cd",
        callout_text="远程校准切换",
        pua_icon="\uE518",
    )
    mods.update(m_ev_r_cd)
    appears.update(a_ev_r_cd)

    # 4. SP1 破甲 (ID: 2426): 每一击 60% 施加 35% 破甲 6 秒，并移除对方所有护甲增益 (由 C 在非格挡 SP1 命中处理)
    m_sp1_ab, a_sp1_ab = make_armor_break_statmod(
        mod_id="bumblebee_cin_dotm_sp1_armor_break",
        duration=6.0,
        break_amount=0.35,
        chance=0.60,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_sp1_armor_break",
        callout_text="破甲",
        show_callout=True,
        pua_icon="\uE516",
    )
    mods.update(m_sp1_ab)
    appears.update(a_sp1_ab)

    # 5. SP2 震击 (ID: 2427): 最后一击 100% 施加 10 秒震击 (基础 80% ATK, 对方有护甲则 +150% -> 200% ATK)
    m_sp2_shk, a_sp2_shk = make_shock_statmod(
        mod_id="bumblebee_cin_dotm_sp2_shock",
        duration=10.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_sp2_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp2_shk)
    appears.update(a_sp2_shk)

    m_sp2_shk_arm, a_sp2_shk_arm = make_shock_statmod(
        mod_id="bumblebee_cin_dotm_sp2_shock_armored",
        duration=10.0,
        total_dmg=float(round(base_atk * 2.00)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_sp2_shock_armored",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp2_shk_arm)
    appears.update(a_sp2_shk_arm)

    # 6. SP3 震击 (ID: 2436): 最后一击 100% 施加 10 秒震击 (基础 80% ATK, 对方有护甲则 +100% -> 160% ATK)
    m_sp3_shk, a_sp3_shk = make_shock_statmod(
        mod_id="bumblebee_cin_dotm_sp3_shock",
        duration=10.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_sp3_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp3_shk)
    appears.update(a_sp3_shk)

    m_sp3_shk_arm, a_sp3_shk_arm = make_shock_statmod(
        mod_id="bumblebee_cin_dotm_sp3_shock_armored",
        duration=10.0,
        total_dmg=float(round(base_atk * 1.60)),
        chance=1.0,
        trigger="",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_sp3_shock_armored",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp3_shk_arm)
    appears.update(a_sp3_shk_arm)

    return mods, appears
