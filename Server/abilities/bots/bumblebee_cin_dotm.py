#!/usr/bin/env python3
"""
Bot Ability Implementation: 电影大黄蜂 (Bumblebee DOTM)
======================================================
Bot ID: bumblebee_cin_dotm
阵营: 汽车人 (Autobot) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 近战校准 / Melee Calibration] (ID: 2421, pua_icon: 0xe509, category: passive)
   - 官方描述: "开局自动获得一个近战规避，无倒计时。25.5%的概率规避对手的近战攻击。如果拥有远程规避时被对手近战攻击击中，则出现灰色的近战规避倒计时图标1.5秒，结束后重新获得近战规避。"
   - 实现方案:
     由 Native C (skill_bumblebee_dotm.c) 管理 CalibrationMode 状态机与 25.5% 近战闪避。

2. [被动 - 远程校准 / Ranged Calibration] (ID: 2422, pua_icon: 0xe518, category: passive)
   - 官方描述: "拥有近战规避时被对手远程攻击击中，近战规避消失，出现灰色的远程规避倒计时图标1.5秒，结束后获得远程规避，无倒计时，25.5%的概率规避对手的远程攻击。近战规避消失。"
   - 实现方案:
     由 Native C (skill_bumblebee_dotm.c) 管理 1.5 秒切换倒计时与 25.5% 远程闪避。

3. [被动 - 击倒攻击增益 / Attack Buff on Knockdown] (ID: 2424, pua_icon: 0xe406, category: passive)
   - 官方描述: "每击倒对手一次：获得一个永久攻击增益，攻击力增加13.5%。永远增益最多堆叠15层，第16层开始出现倒计时，3秒后消失。"
   - 实现方案:
     bumblebee_cin_dotm_knockdown_atk:
       触发 onKnockdownOpponent, 获得攻击力增益 (+13.5% 攻击力)，最多堆叠 15 层 (第16层 3s 倒计时)，
       金色血条圆环图标 (PUA: 0xe406, Hex: F59E0B / D97706), 呼出文字: "攻击加成"。
-----------------------------------------------------------------------------
"""

from ..core import make_attack_boost_statmod, make_evade_grant_statmod
from ..registry import register_bot

BOT_ID = "bumblebee_cin_dotm"


@register_bot(BOT_ID, name_zh="电影大黄蜂", desc="战术系核心特工，近战/远程校准自适应双模规避，击倒对手永久叠加攻击力")
def build_bumblebee_cin_dotm_abilities(base_hp: float = 30000.0, base_atk: float = 2380.0):
    mods = {}
    appears = {}

    # 1. 击倒攻击增益 (ID: 2424): 每次击倒对手获得 13.5% 攻击力 (最多 15 层)
    m_kd, a_kd = make_attack_boost_statmod(
        mod_id="bumblebee_cin_dotm_knockdown_atk",
        duration=0.0,  # 永久堆叠
        attack_bonus=0.135,
        chance=1.0,
        trigger="onHit",
        trigger_scope="isLastHit=true",
        appr_id="appr_bumblebee_cin_dotm_knockdown_atk",
        callout_text="击倒增益",
    )
    mods["bumblebee_cin_dotm_knockdown_atk"] = m_kd
    appears["appr_bumblebee_cin_dotm_knockdown_atk"] = a_kd

    # 2. 开局近战校准常驻规避 (ID: 2421)
    m_ev_m, a_ev_m = make_evade_grant_statmod(
        mod_id="bumblebee_cin_dotm_calib_melee",
        evade_type="melee",
        grant_chance=1.0,
        evade_chance=0.255,
        duration=0.0,  # 常驻无倒计时
        trigger="onFightStart",
        trigger_scope=None,
        appr_id="appr_bumblebee_cin_dotm_calib_melee",
        callout_text="近战校准",
    )
    mods["bumblebee_cin_dotm_calib_melee"] = m_ev_m
    appears["appr_bumblebee_cin_dotm_calib_melee"] = a_ev_m

    # 3. 远程校准规避 (ID: 2422)
    m_ev_r, a_ev_r = make_evade_grant_statmod(
        mod_id="bumblebee_cin_dotm_calib_ranged",
        evade_type="ranged",
        grant_chance=1.0,
        evade_chance=0.255,
        duration=0.0,
        trigger="onFightStart",
        trigger_scope=None,
        appr_id="appr_bumblebee_cin_dotm_calib_ranged",
        callout_text="远程校准",
    )
    mods["bumblebee_cin_dotm_calib_ranged"] = m_ev_r
    appears["appr_bumblebee_cin_dotm_calib_ranged"] = a_ev_r

    return mods, appears
