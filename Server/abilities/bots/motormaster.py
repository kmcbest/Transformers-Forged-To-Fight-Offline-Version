#!/usr/bin/env python3
"""
Bot Ability Implementation: 汽车大师 (Motormaster)
=================================================
Bot ID: motormaster_gs_voyager2015
阵营: 霸天虎 (Decepticon) | 职业: 格斗系 (Brawler)

【官方技能真理源对照 (来自 character_abilities / priority_abilities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 前冲 / Dashing]
   - 官方描述: "汽车大师以不可阻挡的力量向前冲锋，无视对手攻击的影响。"
   - 实现方案: motormaster_dash_unstoppable (0.55s 霸体)

2. [特殊技 2 - 大师级工艺 / A Master Craft]
   - 官方描述: "获得4秒的不可阻挡"
   - 实现方案: motormaster_sp2_unstoppable (4.0s 霸体)

3. [被动 - 重击冲压 / Heavy Ram] (ID: 3180, pua_icon: 0xe516)
   - 官方描述: "用重击撞击对手时随机造成三个减益效果之一（均持续6秒）: 21.6%攻击减益, 29.7%破甲减益, 24.3%能量功率减益"

4. [觉醒技 - 公路之王 / King of the Road] (ID: 3184, pua_icon: 0xe406)
   - 官方描述: "每损失最大生命值的20%，得到1层60%的近战增益。最多4层无倒计时。"

5. [特殊技 3 - 伤害爆发与反冲 / SP3 Recoil Blast] (ID: 3187, pua_icon: 0xe406)
   - 官方描述: "最后一击伤害增加150%，但同时对自身造成攻击力90%的伤害（留1点体力不自杀）。"

6. [特殊技 1 - 能量燃烧 / SP1 Power Burn] (ID: 3535, pua_icon: 0xe607)
   - 官方描述: "即时扣除对方最大能量的2%"

7. [特殊技 3 - 冲压全开 / SP3 Full Ram] (ID: 3536, pua_icon: 0xe516)
   - 官方描述: "最后一击施加冲压减益: 21.6%攻击减益, 29.7%破甲减益, 24.3%能量功率减益，持续6秒"
-----------------------------------------------------------------------------
"""

from ..core import (
    make_unstoppable_statmod,
    make_attack_boost_statmod,
    make_armor_break_statmod,
    make_power_leak_statmod,
    validate_statmod,
    validate_appear,
    validate_color_code,
)
from ..registry import register_bot

BOT_ID = "motormaster_gs_voyager2015"


@register_bot(BOT_ID, name_zh="汽车大师", desc="格斗系，前冲与SP2不可阻挡霸体、重击冲压随机三重削弱、公路之王残血近战爆发、SP1烧能与SP3舍身轰击")
def build_motormaster_abilities(base_hp: float = 34894.0, base_atk: float = 2629.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 前冲霸体 (Dashing Unstoppable, 0.55s)
    # -------------------------------------------------------------------------
    m_dash, a_dash = make_unstoppable_statmod(
        mod_id="motormaster_dash_unstoppable",
        duration=0.55,
        trigger="onPlayerStateEnter",
        trigger_scope="state=Dash",
        appr_id="appr_motormaster_dash_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        play_vfx=True,
        vfx_move="status_unstoppable",
    )
    m_dash["motormaster_dash_unstoppable"]["t"] = "buff"
    mods.update(m_dash)
    appears.update(a_dash)

    # -------------------------------------------------------------------------
    # 2. SP2 4秒霸体 (Special Attack 2 Unstoppable, 4.0s)
    # -------------------------------------------------------------------------
    m_sp2, a_sp2 = make_unstoppable_statmod(
        mod_id="motormaster_sp2_unstoppable",
        duration=4.0,
        trigger="onSpecial2Activate",
        trigger_scope="",
        appr_id="appr_motormaster_sp2_unstoppable",
        callout_text="不可阻挡",
        show_callout=True,
        play_vfx=True,
        vfx_move="status_unstoppable",
    )
    mods.update(m_sp2)
    appears.update(a_sp2)

    # -------------------------------------------------------------------------
    # 3. 重击冲压 (ID: 3180): 随机施加 21.6%减攻 / 29.7%破甲 / 24.3%减能 (6s)
    # -------------------------------------------------------------------------
    m_ram_atk, a_ram_atk = make_attack_boost_statmod(
        mod_id="motormaster_heavy_atk_debuff",
        duration=6.0,
        attack_bonus=-0.216,
        chance=0.333,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_motormaster_heavy_atk_debuff",
        callout_text="冲压减攻",
        pua_icon="\uE516",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    m_ram_atk["motormaster_heavy_atk_debuff"]["ta"] = "opponent"
    m_ram_atk["motormaster_heavy_atk_debuff"]["mt"] = "debuff"
    m_ram_atk["motormaster_heavy_atk_debuff"]["t"] = "attack_debuff"
    mods.update(m_ram_atk)
    appears.update(a_ram_atk)

    m_ram_arm, a_ram_arm = make_armor_break_statmod(
        mod_id="motormaster_heavy_armor_break",
        duration=6.0,
        break_amount=0.297,
        chance=0.333,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_motormaster_heavy_armor_break",
        callout_text="冲压破甲",
        pua_icon="\uE516",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_ram_arm)
    appears.update(a_ram_arm)

    m_ram_pow, a_ram_pow = make_power_leak_statmod(
        mod_id="motormaster_heavy_power_leak",
        duration=6.0,
        drain_bars=0.243,
        chance=0.334,
        trigger="onHit",
        trigger_scope="level=Heavy",
        appr_id="appr_motormaster_heavy_power_leak",
        callout_text="冲压控能",
        pua_icon="\uE607",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_ram_pow)
    appears.update(a_ram_pow)

    # -------------------------------------------------------------------------
    # 4. 觉醒技 - 公路之王 (ID: 3184): 每损血 20% 获得 60% 近战增益 (最多4层)
    # -------------------------------------------------------------------------
    m_king, a_king = make_attack_boost_statmod(
        mod_id="motormaster_king_of_road",
        duration=0.0,
        attack_bonus=0.60,
        chance=1.0,
        trigger="onPlayerStateEnter",
        trigger_scope="hp_step=0.20",
        appr_id="appr_motormaster_king_of_road",
        callout_text="公路之王",
        pua_icon="\uE406",
        color_hex="FF8800",
        gradient_bottom="D97706",
        stackable=True,
        max_stacks=4,
    )
    mods.update(m_king)
    appears.update(a_king)

    # -------------------------------------------------------------------------
    # 5. 特殊技 3 - 伤害爆发与反冲自伤 (ID: 3187)
    # 最后一击伤害 +150%，但对自身造成攻击力 90% 伤害 (留1点血)
    # -------------------------------------------------------------------------
    m_sp3_burst, a_sp3_burst = make_attack_boost_statmod(
        mod_id="motormaster_sp3_burst_atk",
        duration=0.0,
        attack_bonus=1.50,
        chance=1.0,
        trigger="onSpecial3Activate",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_motormaster_sp3_burst_atk",
        callout_text="爆发",
        pua_icon="\uE406",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_sp3_burst)
    appears.update(a_sp3_burst)

    mod_recoil = {
        "id": "motormaster_sp3_self_recoil",
        "t": "recoil_damage",
        "tm": "",
        "tr": ["onSpecial3Activate"],
        "uit": ["onSpecial3Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "dmgFlags=LastHit",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.90,
        "d": 0.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_recoil)
    mods["motormaster_sp3_self_recoil"] = mod_recoil

    # -------------------------------------------------------------------------
    # 6. 特殊技 1 - 能量燃烧 (ID: 3535): 即时扣除对方 2% 最大能量
    # -------------------------------------------------------------------------
    m_sp1_burn, a_sp1_burn = make_power_leak_statmod(
        mod_id="motormaster_sp1_power_burn",
        duration=0.0,
        drain_bars=0.02,
        chance=1.0,
        trigger="onSpecial1Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_motormaster_sp1_burn",
        callout_text="能量燃烧",
        pua_icon="\uE607",
        color_hex="FF8800",
        gradient_bottom="D97706",
    )
    mods.update(m_sp1_burn)
    appears.update(a_sp1_burn)

    # -------------------------------------------------------------------------
    # 7. 特殊技 3 - 冲压全开 (ID: 3536): 最后一击施加持续 6 秒冲压减益
    # -------------------------------------------------------------------------
    m_sp3_ram, a_sp3_ram = make_armor_break_statmod(
        mod_id="motormaster_sp3_ram_armor",
        duration=6.0,
        break_amount=0.297,
        chance=1.0,
        trigger="onSpecial3Hit",
        trigger_scope="dmgFlags=LastHit",
        appr_id="appr_motormaster_sp3_ram_armor",
        callout_text="冲压破甲",
        pua_icon="\uE516",
        color_hex="EF4444",
        gradient_bottom="B91C1C",
    )
    mods.update(m_sp3_ram)
    appears.update(a_sp3_ram)

    return mods, appears, buffs
