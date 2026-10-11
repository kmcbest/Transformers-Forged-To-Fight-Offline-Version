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
     bumblebee_cin_dotm_calib_melee:
       触发 onFightStart, 获得常驻近战规避 buff (25.5% 规避几率),
       配合 Native C (skill_bumblebee_dotm.c) 实现受远程攻击后 1.5s 切换到远程校准。

2. [被动 - 远程校准 / Ranged Calibration] (ID: 2422, pua_icon: 0xe518, category: passive)
   - 官方描述: "拥有近战规避时被对手远程攻击击中，近战规避消失，出现灰色的远程规避倒计时图标1.5秒，结束后获得远程规避，无倒计时，25.5%的概率规避对手的远程攻击。近战规避消失。"
   - 实现方案:
     bumblebee_cin_dotm_calib_ranged:
       作为切换后获得的常驻远程规避 buff (25.5% 规避几率),
       配合 Native C (skill_bumblebee_dotm.c) 实现受近战攻击后 1.5s 切换到近战校准。

3. [被动 - 击倒攻击增益 / Attack Buff on Knockdown] (ID: 2424, pua_icon: 0xe406, category: passive)
   - 官方描述: "每击倒对手一次：获得一个永久攻击增益，攻击力增加13.5%。永远增益最多堆叠15 层，第16层开始出现倒计时，3秒后消失。"
   - 实现方案:
     bumblebee_cin_dotm_knockdown_atk:
       触发 onHit, isLastHit=true (重击或必杀技末击造成击倒),
       获得永久攻击增益 (+13.5% 攻击力)，最多堆叠 15 层。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_evade_grant_statmod,
)
from ..registry import register_bot

BOT_ID = "bumblebee_cin_dotm"


@register_bot(BOT_ID, name_zh="大黄蜂", desc="战术系特工，双模校准规避对手近战/远程攻击，击倒对手无上限叠加攻击增益")
def build_bumblebee_cin_dotm_abilities(base_hp: float = 28550.0, base_atk: float = 2280.0):
    mods = {}
    appears = {}

    # 1. 击倒对手获得永久攻击增益 (+13.5% 攻击力)，最多 15 层
    m_kd, a_kd = make_attack_boost_statmod(
        mod_id="bumblebee_cin_dotm_knockdown_atk",
        duration=0.0,  # 永久常驻
        attack_bonus=0.135,
        chance=1.0,
        trigger="onHit",
        trigger_scope="isLastHit=true;level=Heavy,Special1,Special2,Special3",
        appr_id="appr_bumblebee_cin_dotm_knockdown_atk",
        callout_text="攻击加成",
        show_callout=True,
        pua_icon="\uE406",
        color_hex="F59E0B",
        gradient_bottom="D97706",
        stackable=True,
        max_stacks=15,
    )
    mods.update(m_kd)
    appears.update(a_kd)

    # 2. 近战校准规避 (ID: 2421): 开局自动获得近战规避 (常驻无倒计时, 25.5% 规避率)
    m_ev_m, a_ev_m = make_evade_grant_statmod(
        mod_id="bumblebee_cin_dotm_calib_melee",
        evade_type="melee",
        grant_chance=1.0,
        evade_chance=0.255,
        duration=0.0,  # 常驻无倒计时
        trigger="always",
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_calib_melee",
        callout_text="近战校准",
        show_callout=True,
    )
    mods.update(m_ev_m)
    appears.update(a_ev_m)

    # 3. 远程校准规避 (ID: 2422): 受到远程攻击切换为远程校准 (常驻无倒计时, 25.5% 规避率)
    m_ev_r, a_ev_r = make_evade_grant_statmod(
        mod_id="bumblebee_cin_dotm_calib_ranged",
        evade_type="ranged",
        grant_chance=1.0,
        evade_chance=0.255,
        duration=0.0,
        trigger="onPreDamage",
        trigger_scope="level=Ranged",
        appr_id="appr_bumblebee_cin_dotm_calib_ranged",
        callout_text="远程校准",
        show_callout=True,
    )
    mods.update(m_ev_r)
    appears.update(a_ev_r)

    return mods, appears
