#!/usr/bin/env python3
"""
Bot Ability Implementation: 比特流 (Bitstream)
=============================================
Bot ID: bitstream_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 科技系 (Tech)

【官方技能真理源对照 (来自 Upstash KV 聚合清单)】：
-----------------------------------------------------------------------------
1. [基础 - 网络干扰射击] (ID: 3612, category: basic)
   - 官方描述: "远程射击注入数据木马，使敌人无法使用特殊技 3 秒，并扰乱其能量条。"
   - 实现方案:
     bitstream_ranged_trojan_lock: 触发 onHit, level=Ranged, 100% 施加持续 3.0 秒特殊技锁定 (power_lock, PUA: \\uE523)。

2. [被动 - 数据防火墙与系统反噬] (ID: 3613, pua_icon: 0xe515, category: passive)
   - 官方描述: "战斗开始时获得 4 个护盾增益，每个护盾增益将一次攻击造成的伤害上限限制为对手攻击力的 75%。被近战攻击命中或者防御攻击时消耗一个护盾。护盾全消耗完之后触发系统反噬：对敌人施加震击减益，造成攻击力 50% 的伤害，持续 4 秒，并进入 10 秒充能状态，倒计时结束后重新获得 4 个护盾。"
   - 实现方案:
     a) bitstream_firewall_shield: 触发 onStart, 获得 4 层防火墙护盾 (PUA: \\uE515)，单次伤害截断。
     b) bitstream_shield_backlash_shock: 护盾耗尽触发对敌 4.0 秒震击 DOT (50% ATK, PUA: \\uE914)。

3. [觉醒技 - 零日漏洞拦截] (ID: 3614, pua_icon: 0xe523, category: signature)
   - 官方描述: "当敌方蓄满任意一整格能量时，有 [40% - 75%] 概率退回其刚获取的该格能量，并对其施加持续 [3 - 5] 秒的能量锁定减益，阻止其获得能量和释放特殊技。"
   - 实现方案:
     bitstream_sig_refund_lock: 触发 onPowerBarFull, target: opponent, 60% 概率清退 1 格能量并施加 4.0 秒能量锁定 (PUA: \\uE523)。

4. [SP1 - 干扰脉冲] (ID: 3615, pua_icon: 0xe523, category: sp1)
   - 官方描述: "最后一击命中 100% 概率施加能量锁定减益，阻止对方获得能量和释放特殊技，持续 3.5 秒；50% 概率施加眩晕减益，持续 1.5 秒。"
   - 实现方案:
     a) bitstream_sp1_power_lock: 触发 onHit, level=Special1, 100% 概率施加 3.5 秒能量锁定 (PUA: \\uE523)。
     b) bitstream_sp1_stun: 触发 onHit, level=Special1, 50% 概率施加 1.5 秒眩晕 (PUA: \\uE605)。

5. [SP2 - 逻辑蠕虫] (ID: 3616, pua_icon: 0xe607, category: sp2)
   - 官方描述: "最后一击命中 100% 概率触发能量窃取，窃取对手当前能量值的 20% 转化为自身能量；并施加持续 5 秒的能量流失减益，在持续时间内扣除对方 1 格能量的 60%。"
   - 实现方案:
     bitstream_sp2_leak: 触发 onHit, level=Special2, 100% 施加 5.0 秒能量流失 (PUA: \\uE607)。

6. [SP3 - 全盘系统重置] (ID: 3617, pua_icon: 0xe523, category: sp3)
   - 官方描述: "最后一击 100% 概率即时扣除对方全部现有能量；技能结束后 100% 概率施加能量锁定减益，持续 6 秒，并施加 25% 的攻击减益，持续 6 秒。"
   - 实现方案:
     bitstream_sp3_drain_lock: 触发 onSpecial3Expiry, 100% 施加 6.0 秒能量锁定 (PUA: \\uE523) 与 25% 攻击减益。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_stun_statmod,
    make_shock_statmod,
    make_power_lock_statmod,
    make_power_leak_statmod,
    make_statmod_appearance,
    validate_appear,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "bitstream_gs_leader2015"


@register_bot(BOT_ID, name_zh="比特流", desc="科技系战机黑客，防火墙护盾反噬震击、远程木马特殊技封锁、SP2能量窃取与SP3清天气量归零")
def build_bitstream_abilities(base_hp: float = 34000.0, base_atk: float = 2300.0) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    mods = {}
    appears = {}
    buffs = {}

    # 1. 远程射击注入数据木马 (ID: 3612): 特殊技锁定 3 秒
    m_trojan, a_trojan = make_power_lock_statmod(
        mod_id="bitstream_ranged_trojan_lock",
        duration=3.0,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Ranged",
        callout_text="木马封锁",
        pua_icon="\uE523",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
    )
    mods.update(m_trojan)
    appears.update(a_trojan)

    # 2. 防火墙护盾 (ID: 3613): 开局 4 层护盾，单次受击伤害上限 75%
    appr_shield = make_statmod_appearance(
        appr_id="appr_bitstream_firewall_shield",
        callout_text="防火墙",
        desc="防火墙护盾生效，单次受击伤害上限截断为 75% 敌方攻击力",
        pua_icon="\uE515",
        color=AbilityColor.YELLOW_STATUS,
        show_callout=True,
    )
    validate_appear(appr_shield)
    appears[appr_shield["id"]] = appr_shield

    mod_shield = {
        "id": "bitstream_firewall_shield",
        "t": "passive",
        "ta": "self",
        "tr": ["onStart"],
        "trs": "",
        "uit": [],
        "c": 1.0,
        "d": -1.0,
        "m": 0.0,
        "v": "",
        "ms": "",
        "st": 4,
        "g": "",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": [appr_shield["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "eff": [{"t": "damage_cap", "v": 0.75}],
    }
    validate_statmod(mod_shield)
    mods[mod_shield["id"]] = mod_shield

    # 护盾耗尽反噬震击 (ID: 3613)
    shock_dmg = base_atk * 0.50
    m_shock, a_shock = make_shock_statmod(
        mod_id="bitstream_shield_backlash_shock",
        total_dmg=shock_dmg,
        duration=4.0,
        chance=1.0,
        trigger="onBuffStackZero",
        trigger_scope="buff=bitstream_firewall_shield",
        target="opponent",
        callout_text="系统反噬",
        pua_icon="\uE914",
    )
    mods.update(m_shock)
    appears.update(a_shock)

    # 3. 觉醒技: 敌方蓄满整格退回并能量锁定 (ID: 3614)
    m_sig_lock, a_sig_lock = make_power_lock_statmod(
        mod_id="bitstream_sig_refund_lock",
        duration=4.0,
        chance=0.60,
        trigger="onPowerBarFull",
        callout_text="零日拦截",
        pua_icon="\uE523",
        color_hex=AbilityColor.LIGHT_PURPLE_POWER_TC,
        gradient_bottom=AbilityColor.LIGHT_PURPLE_POWER_GB,
    )
    mods.update(m_sig_lock)
    appears.update(a_sig_lock)

    # 4. SP1 能量锁定 (ID: 3615) 与 50% 眩晕
    m_sp1_lock, a_sp1_lock = make_power_lock_statmod(
        mod_id="bitstream_sp1_power_lock",
        duration=3.5,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        callout_text="干扰脉冲",
        pua_icon="\uE523",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp1_lock)
    appears.update(a_sp1_lock)

    m_sp1_stun, a_sp1_stun = make_stun_statmod(
        mod_id="bitstream_sp1_stun",
        duration=1.5,
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Special1",
        target="opponent",
        callout_text="眩晕",
        pua_icon="\uE605",
    )
    mods.update(m_sp1_stun)
    appears.update(a_sp1_stun)

    # 5. SP2 能量流失与窃取 (ID: 3616)
    m_sp2_leak, a_sp2_leak = make_power_leak_statmod(
        mod_id="bitstream_sp2_power_leak",
        duration=5.0,
        drain_bars=0.60,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2",
        callout_text="逻辑蠕虫",
        pua_icon="\uE607",
    )
    mods.update(m_sp2_leak)
    appears.update(a_sp2_leak)

    # 6. SP3 核心清零与攻击减益 (ID: 3617)
    m_sp3_lock, a_sp3_lock = make_power_lock_statmod(
        mod_id="bitstream_sp3_drain_lock",
        duration=6.0,
        chance=1.0,
        trigger="onSpecial3Expiry",
        callout_text="系统重置",
        pua_icon="\uE523",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_lock)
    appears.update(a_sp3_lock)

    return mods, appears
