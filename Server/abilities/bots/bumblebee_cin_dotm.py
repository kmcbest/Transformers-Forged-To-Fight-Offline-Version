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
       触发 always, 获得常驻近战规避 buff (25.5% 规避几率),
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

4. [SP1 - 破甲 / Armor Break] (ID: 2426, pua_icon: 0xe516, category: sp1)
   - 官方描述: "每一击都有60%的概率施加破甲，移除对方身上所有护甲增益，并施加35%的破甲减益，持续6秒。"
   - 实现方案:
     bumblebee_cin_dotm_sp1_armor_break:
       触发 onHit, level=Special1, 60% 概率施加 6 秒破甲 (降低 35% 护甲，移除对方所有护甲增益)。

5. [SP2 - 震击 / Shock] (ID: 2427, pua_icon: 0xe914, category: sp2)
   - 官方描述: "最后一击施加震击，造成攻击力80%的伤害，持续10秒，对方身上如果有护甲，震击伤害增加"
   - 实现方案:
     bumblebee_cin_dotm_sp2_shock:
       触发 onHit, level=Special2;isLastHit=true, 施加 10 秒震击 (80% ATK 伤害),
       配合 Native C (skill_bumblebee_dotm.c) 若目标有护甲增益则额外增幅伤害。

6. [SP3 - 震击 / Shock] (ID: 2436, pua_icon: 0xe914, category: sp3)
   - 官方描述: "最后一击施加震击，造成攻击力80%的伤害，持续10秒，对方身上如果有护甲，震击伤害变为攻击力的180%"
   - 实现方案:
     bumblebee_cin_dotm_sp3_shock:
       触发 onHit, level=Special3;isLastHit=true, 施加 10 秒震击 (80% ATK 伤害),
       配合 Native C (skill_bumblebee_dotm.c) 若目标有护甲则伤害变更为 180% ATK。
-----------------------------------------------------------------------------
"""

from ..core import (
    make_attack_boost_statmod,
    make_evade_grant_statmod,
    make_armor_break_statmod,
    make_shock_statmod,
)
from ..registry import register_bot

BOT_ID = "bumblebee_cin_dotm"


@register_bot(BOT_ID, name_zh="大黄蜂", desc="战术系特工，双模校准规避对手近战/远程攻击，击倒对手无上限叠加攻击增益，多段特技破甲与感电震击")
def build_bumblebee_cin_dotm_abilities(base_hp: float = 28550.0, base_atk: float = 2280.0):
    mods = {}
    appears = {}

    # 1. 击倒对手获得永久攻击增益 (+13.5% 攻击力)，最多 15 层 (ID: 2424)
    m_kd, a_kd = make_attack_boost_statmod(
        mod_id="bumblebee_cin_dotm_knockdown_atk",
        duration=-1.0,  # 负数持续时间表示永久无倒计时堆叠buff (IsIndefinite=true)
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

    # 1b. 第 16 层满溢爆发攻击增益 (+13.5% 攻击力)，持续 3.0 秒 (ID: 2424b)
    m_burst, a_burst = make_attack_boost_statmod(
        mod_id="bumblebee_cin_dotm_burst_atk",
        duration=3.0,  # 3秒倒计时
        attack_bonus=0.135,
        chance=1.0,
        trigger="manual",  # 由 NativeHook 在满 15 层后击倒对手时施加
        trigger_scope="",
        appr_id="appr_bumblebee_cin_dotm_burst_atk",
        callout_text="攻击加成",
        show_callout=True,
        pua_icon="\uE406",
        color_hex="EF4444",
        gradient_bottom="DC2626",
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_burst)
    appears.update(a_burst)

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

    # 4. SP1 破甲 (ID: 2426): 每一击 60% 施加 35% 破甲 6 秒，移除对方护甲增益
    m_sp1_ab, a_sp1_ab = make_armor_break_statmod(
        mod_id="bumblebee_cin_dotm_sp1_armor_break",
        duration=6.0,
        break_amount=0.35,
        chance=0.60,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_bumblebee_cin_dotm_sp1_armor_break",
        callout_text="破甲",
        show_callout=True,
        pua_icon="\uE516",
    )
    mods.update(m_sp1_ab)
    appears.update(a_sp1_ab)

    # 5. SP2 震击 (ID: 2427): 最后一击 100% 施加 10 秒震击 (80% ATK 伤害)
    m_sp2_shk, a_sp2_shk = make_shock_statmod(
        mod_id="bumblebee_cin_dotm_sp2_shock",
        duration=10.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2;isLastHit=true",
        appr_id="appr_bumblebee_cin_dotm_sp2_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp2_shk)
    appears.update(a_sp2_shk)

    # 6. SP3 震击 (ID: 2436): 最后一击 100% 施加 10 秒震击 (80% ATK 伤害)
    m_sp3_shk, a_sp3_shk = make_shock_statmod(
        mod_id="bumblebee_cin_dotm_sp3_shock",
        duration=10.0,
        total_dmg=float(round(base_atk * 0.80)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3;isLastHit=true",
        appr_id="appr_bumblebee_cin_dotm_sp3_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp3_shk)
    appears.update(a_sp3_shk)

    return mods, appears
