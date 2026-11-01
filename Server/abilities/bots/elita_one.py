#!/usr/bin/env python3
"""
Bot Ability Implementation: 艾丽塔 (Elita-1)
===========================================
Bot ID: elita_one_gs / elita_one_gs_kabam
阵营: 汽车人 (Autobot) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 character_abilities 数据库与在线优先实现)】：
-----------------------------------------------------------------------------
1. [被动 - 战术洞察 / Tactical Insight] (ID: 4001, pua_icon: E509)
   - 官方描述: "100%概率规避不可阻挡状态对手的近战攻击，并获得30%的近战增益，持续3秒。"
   - 实现方案:
     a) elita_tactical_insight_evade: 对战不可阻挡敌人时 100% 几率近战规避 (opponent:unstoppable=true;level=Melee)。
     b) elita_tactical_insight_melee_buff: 规避后获得 30% 近战增益持续 3 秒。

2. [被动 - 灵动反击 / Nimble Counter] (ID: 4002, pua_icon: E50A)
   - 官方描述: "闪避对手前冲攻击或近战攻击时，有50%的概率得到一个反击锦囊，持续1秒，
     此时间内如果击中对手，可将对手眩晕1.5秒；如果攻击被对手闪避，则对对手施加1层50%的攻击减益，持续3秒。"
   - 实现方案:
     c) elita_counter_pouch_buff: 闪避冲锋或近战攻击时 50% 获得反击锦囊持续 1.0 秒 (黄色图标 E50A)。
     d) elita_counter_stun: 持有反击锦囊击中对手时造成 1.5 秒眩晕。
     e) elita_counter_atk_debuff: 持有反击锦囊被对手规避时对对手施加 50% 攻击减益持续 3.0 秒。

3. [被动 - 关节狙击 / Joint Aim] (ID: 4003, pua_icon: E409)
   - 官方描述: "远程攻击100%护甲穿透\n远程攻击命中或被防均有70%概率刷新对手身上的减益持续时间。"
   - 实现方案:
     f) elita_joint_aim_pierce: 远程射击 100% 护甲穿透 (level=Ranged)。
     g) elita_joint_aim_refresh: 远程攻击命中或被防御 70% 几率刷新对手身上的减益持续时间。

4. [被动 - 破甲 / Armor Break] (ID: 4017, pua_icon: E516)
   - 官方描述: "远程暴击命中时施加1层50%的破甲减益，持续6秒，最大叠加1层。"
   - 实现方案:
     h) elita_ranged_crit_armor_break: 远程暴击命中施加 50% 破甲持续 6 秒，最大 1 层。

5. [被动 - 领袖威仪 / Commander's Presence] (ID: 4005, pua_icon: 0xe41f)
   - 官方描述: "受到DOT伤害时，每击中对手一次，DOT倒计时加速20%。"
   - 实现方案:
     i) elita_commanders_presence: 受到 DOT 伤害期间每次命中对手加速 DOT 倒计时 20%。

6. [觉醒技 - 抵抗军之火 / Resistance Flame] (ID: 4007, pua_icon: E942)
   - 官方描述: "生命值首次低于50%时激活1层50%的攻击增益和1层50%的暴击率增益，持续6秒。
     生命值首次低于25%时激活1层90%的护甲增益，持续6秒
     生命值低于25%时，对手释放特殊技1或2，有40%的概率被打断，进入眩晕状态1.5秒，每局只能触发一次。对斗士系角色概率为70%。"
   - 实现方案:
     j) elita_sig_flame_atk_50: HP 首次低于 50% 激活 50% 攻击增益持续 6 秒。
     k) elita_sig_flame_crit_50: HP 首次低于 50% 激活 50% 暴击率增益持续 6 秒。
     l) elita_sig_flame_armor_25: HP 首次低于 25% 激活 90% 护甲增益持续 6 秒。
     m) elita_sig_flame_interrupt_stun: HP 低于 25% 时对手释放 SP1/SP2 40% 几率打断并眩晕 1.5 秒。
     n) elita_sig_flame_interrupt_stun_braw: 对斗士系额外增加 30% 打断眩晕几率 (达到 70%)。

7. [SP1 - 破甲 / Armor Break] (ID: 4009, pua_icon: E516)
   - 官方描述: "最后一击命中100%施加35%的破甲减益，持续 7 秒；对阵斗士系时破甲提升至50%。"
   - 实现方案:
     o) elita_sp1_armor_break: SP1 最后一击命中施加 35% 破甲持续 7 秒。
     p) elita_sp1_armor_break_braw: 对阵斗士系追加 15% 额外破甲 (达 50%)。

8. [SP1 - 能量燃烧 / Power Burn] (ID: 4010, pua_icon: 0xe607)
   - 官方描述: "如果对方3格能量满，则最后一击命中时立即扣除其最大能量的5%。"
   - 实现方案:
     q) elita_sp1_power_burn: 对手 3 格满能量时扣除其 5% 能量 (0.15 格)。

9. [SP2 - 驱散 / Nullify] (ID: 4011, pua_icon: 0xe950)
   - 官方描述: "每1击有80%的驱散对手1层护甲、护盾或攻击增益。"
   - 实现方案:
     r) elita_sp2_nullify: SP2 每击 80% 概率驱散对手 1 层护甲、护盾或攻击增益。

10. [SP2 - 震击 / Shock] (ID: 4018, pua_icon: 0xe914)
    - 官方描述: "最后一击100%的概率施加震击，造成攻击100%的伤害，持续10秒。"
    - 实现方案:
      s) elita_sp2_shock: SP2 最后一击 100% 施加持续 10 秒 100% ATK 震击能量伤害。

11. [SP3 - 流血 / Bleed] (ID: 4013, pua_icon: 0xe401)
    - 官方描述: "最后一击施加流血，造成攻击力120%的伤害，持续6秒。"
    - 实现方案:
      t) elita_sp3_bleed: SP3 最后一击施加持续 6 秒 120% ATK 流血伤害。

12. [SP3 - 战术封锁 / Tactical Lockdown] (ID: 4014, pua_icon: E419)
    - 官方描述: "技能结束后封印对手全部特殊攻击8秒。"
    - 实现方案:
      u) elita_sp3_tactical_lockdown: SP3 结束后封印对手特殊攻击 8 秒。

13. [协同 - 永恒誓言 / Eternal Bond] (ID: 4015, pua_icon: E815)
    - 官方描述: "战斗开始时，获得相当于自身最大生命值15%的能量护盾，优先承受普通攻击的伤害，直到消耗完。"
    - 实现方案:
      v) elita_synergy_eternal_bond_shield: 开局获得 15% base_hp 能量护盾。

14. [协同 - 抵抗军姐妹 / Resistance Sisters] (ID: 4016, pua_icon: 0xe40d)
    - 官方描述: "暴击率额外提升10%，重击伤害增益25%。"
    - 实现方案:
      w) elita_synergy_sisters_crit: 常驻提升 10% 暴击率。
      x) elita_synergy_sisters_heavy: 重击攻击力提升 25%。
-----------------------------------------------------------------------------
"""

from typing import Dict, Any, Tuple
from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_shock_statmod,
    make_power_leak_statmod,
    make_power_lock_statmod,
    make_stun_statmod,
    make_nullify_statmod,
    make_evade_grant_statmod,
    make_crit_rate_statmod,
    make_armor_up_statmod,
    make_armor_break_statmod,
    make_attack_boost_statmod,
    make_statmod_appearance,
    validate_statmod,
    validate_appear,
)
from ..registry import register_bot

BOT_ID = "elita_one_gs"
BOT_ID_ALIAS = "elita_one_gs_kabam"


def _build_elita_abilities_impl(
    base_hp: float = 38400.0,
    base_atk: float = 2780.0,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    根据基准属性生成艾丽塔 (Elita-1) 全部专属能力修饰器。
    基准 5星50级 HP = 38400.0, ATK = 2780.0
    """
    mods = {}
    appears = {}
    buffs = {
        # 流血效果
        "dmg_bleed": {
            "id": "dmg_bleed",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "damage_over_time",
            "group": "dmg_bleed",
            "p": {},
        },
        # 震击效果
        "dmg_shock": {
            "id": "dmg_shock",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "multiplier",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "damage_over_time",
            "group": "dmg_shock",
            "p": {},
        },
        # 破甲效果
        "armor_break": {
            "id": "armor_break",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "additive",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "debuff",
            "group": "armor_break",
            "p": {},
        },
        # 能量燃烧/能量流失
        "power_leak": {
            "id": "power_leak",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "additive",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "debuff",
            "group": "power_leak",
            "p": {},
        },
        # 特殊攻击封印/能量锁定
        "power_lock": {
            "id": "power_lock",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "power_lock",
            "group": "power_lock",
            "p": {},
        },
        # 眩晕
        "stun": {
            "id": "stun",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "stun",
            "group": "stun",
            "p": {},
        },
        # 护甲提升
        "armor_up": {
            "id": "armor_up",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "additive",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "armor_up",
            "p": {},
        },
        # 攻击力提升
        "attack_buff": {
            "id": "attack_buff",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "additive",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "attack_buff",
            "p": {},
        },
        # 攻击减益
        "attack_debuff": {
            "id": "attack_debuff",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "additive",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "debuff",
            "group": "attack_debuff",
            "p": {},
        },
        # 暴击几率提升
        "crit_rate": {
            "id": "crit_rate",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "additive",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "crit_rate",
            "p": {},
        },
        # 反击锦囊状态
        "elita_counter_pouch": {
            "id": "elita_counter_pouch",
            "iconTexture": "",
            "image": "",
            "images3": False,
            "modeAvail": [],
            "scope": "global",
            "valueType": "absolute",
            "displayValue": 1.0,
            "c": 1,
            "value": 1.0,
            "buffType": "buff",
            "group": "status",
            "p": {},
        },
    }

    # =========================================================================
    # 1. [SP1] 等离子疾射 (Plasma Burst)
    #    a) 破甲: 最后一击 100% 施加 35% 破甲持续 7 秒 (对斗士系 50%)
    #    b) 能量燃烧: 对手 3 格满能量时扣除其 5% 能量
    # =========================================================================
    m_sp1_ab, a_sp1_ab = make_armor_break_statmod(
        mod_id="elita_sp1_armor_break",
        duration=7.0,
        break_amount=0.35,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_elita_sp1_ab",
        callout_text="破甲",
        pua_icon="\uE516",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
        stackable=True,
    )
    mods.update(m_sp1_ab)
    appears.update(a_sp1_ab)

    # 针对斗士系追加 15% 破甲 (共计 50%)
    m_sp1_braw, a_sp1_braw = make_armor_break_statmod(
        mod_id="elita_sp1_armor_break_braw",
        duration=7.0,
        break_amount=0.15,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1;opponent:class=braw",
        appr_id="appr_elita_sp1_braw",
        callout_text="战术压制",
        pua_icon="\uE516",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
        stackable=True,
    )
    mods.update(m_sp1_braw)
    appears.update(a_sp1_braw)

    # 能量燃烧: 对手满能量时扣除 5% (0.15 格)
    m_sp1_pb, a_sp1_pb = make_power_leak_statmod(
        mod_id="elita_sp1_power_burn",
        duration=0.5,
        drain_bars=0.15,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special1;opponent:power>=3.0",
        appr_id="appr_elita_sp1_pb",
        callout_text="能量燃烧",
        pua_icon="\uE607",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp1_pb)
    appears.update(a_sp1_pb)

    # =========================================================================
    # 2. [SP2] 混沌舞步 (Chaotic Dance)
    #    a) 驱散: 每击 80% 驱散对手 1 层护甲/护盾/攻击增益
    #    b) 震击: 最后一击 100% 造成攻击力 100% 的震击伤害，持续 10 秒
    # =========================================================================
    m_sp2_null, a_sp2_null = make_nullify_statmod(
        mod_id="elita_sp2_nullify",
        target_categories=["armor_up", "attack_buff", "shield"],
        chance=0.80,
        trigger="onHit",
        trigger_scope="level=Special2",
        appr_id="appr_elita_sp2_null",
        callout_text="驱散",
        pua_icon="\uE950",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp2_null)
    appears.update(a_sp2_null)

    # 震击 10 秒 DOT (100% ATK = 2780.0, 单跳 139.0 > 1.0)
    m_sp2_shk, a_sp2_shk = make_shock_statmod(
        mod_id="elita_sp2_shock",
        duration=10.0,
        total_dmg=float(round(base_atk * 1.00)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special2",
        appr_id="appr_elita_sp2_shk",
        callout_text="震击",
        pua_icon="\uE914",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp2_shk)
    appears.update(a_sp2_shk)

    # =========================================================================
    # 3. [SP3] 塞伯坦和平年代 (Pax Cybertronia)
    #    a) 流血: 最后一击 120% ATK 持续 6 秒 (单跳 278.0 > 1.0)
    #    b) 战术封锁: 技能结束后封印对手全部特殊攻击 8 秒
    # =========================================================================
    m_sp3_bld, a_sp3_bld = make_bleed_statmod(
        mod_id="elita_sp3_bleed",
        duration=6.0,
        total_dmg=float(round(base_atk * 1.20)),
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        appr_id="appr_elita_sp3_bld",
        callout_text="流血",
        pua_icon="\uE401",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_bld)
    appears.update(a_sp3_bld)

    m_sp3_lock, a_sp3_lock = make_power_lock_statmod(
        mod_id="elita_sp3_tactical_lockdown",
        duration=8.0,
        chance=1.0,
        trigger="onHit",
        trigger_scope="level=Special3",
        appr_id="appr_elita_sp3_lock",
        callout_text="战术封锁",
        pua_icon="\uE419",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
    )
    mods.update(m_sp3_lock)
    appears.update(a_sp3_lock)

    # =========================================================================
    # 4. [被动] 战术洞察 (Tactical Insight)
    #    - 100% 规避不可阻挡对手的近战攻击
    #    - 获得 30% 近战增益持续 3 秒
    # =========================================================================
    m_insight_evd, a_insight_evd = make_evade_grant_statmod(
        mod_id="elita_tactical_insight_evade",
        evade_type="melee",
        grant_chance=1.0,
        evade_chance=1.0,
        duration=0.0,
        trigger="onAttacked",
        trigger_scope="opponent:unstoppable=true;level=Melee",
        appr_id="appr_elita_insight_evd",
        callout_text="战术洞察",
        pua_icon="\uE509",
        color_hex=AbilityColor.GREEN_HEALTH_TC,
        gradient_bottom=AbilityColor.GREEN_HEALTH_GB,
    )
    mods.update(m_insight_evd)
    appears.update(a_insight_evd)

    m_insight_buff, a_insight_buff = make_attack_boost_statmod(
        mod_id="elita_tactical_insight_melee_buff",
        duration=3.0,
        attack_bonus=0.30,
        chance=1.0,
        trigger="onEvade",
        trigger_scope="opponent:unstoppable=true",
        appr_id="appr_elita_insight_buff",
        callout_text="近战增益",
        pua_icon="\uE509",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=False,
    )
    mods.update(m_insight_buff)
    appears.update(a_insight_buff)

    # =========================================================================
    # 5. [被动] 灵动反击 (Nimble Counter)
    #    - 闪避冲锋或近战 50% 获得反击锦囊 (持续 1.0s)
    #    - 击中对手眩晕 1.5s
    #    - 被对手闪避施加 50% 攻击削弱持续 3s
    # =========================================================================
    appr_pouch = make_statmod_appearance(
        appr_id="appr_elita_counter_pouch",
        callout_text="反击锦囊",
        desc="闪避后获得反击锦囊，命中可眩晕对手，若被闪避则削弱对手攻击",
        pua_icon="\uE50A",
        color=AbilityColor.YELLOW_STATUS,
        short_desc="反击锦囊",
    )
    appears[appr_pouch["id"]] = appr_pouch
    mods["elita_counter_pouch_buff"] = {
        "id": "elita_counter_pouch_buff",
        "AppearanceID": appr_pouch["id"],
        "Type": "combat",
        "t": "combat",
        "d": 1.0,
        "m": 1.0,
        "p": 0.50,
        "tr": ["onEvade"],
        "trs": "opponent:level=Dash,Run,Melee",
        "uit": ["none"],
        "a": [appr_pouch["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "ta": "self",
        "mt": "buff",
        "s": "none",
        "st": 1,
    }

    m_counter_stn, a_counter_stn = make_stun_statmod(
        mod_id="elita_counter_stun",
        duration=1.5,
        chance=1.0,
        trigger="onHit",
        trigger_scope="self:buff=elita_counter_pouch_buff",
        appr_id="appr_elita_counter_stn",
        callout_text="反击眩晕",
        pua_icon="\uE50A",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m_counter_stn)
    appears.update(a_counter_stn)

    appr_weaken = make_statmod_appearance(
        appr_id="appr_elita_counter_weaken",
        callout_text="攻击减益",
        desc="受到灵动反击削弱，攻击力降低 50%",
        pua_icon="\uE50A",
        color=AbilityColor.RED_DEBUFF,
        short_desc="攻击减益",
    )
    appears[appr_weaken["id"]] = appr_weaken
    mods["elita_counter_atk_debuff"] = {
        "id": "elita_counter_atk_debuff",
        "AppearanceID": appr_weaken["id"],
        "Type": "combat",
        "t": "mod_attack_rating",
        "d": 3.0,
        "m": -0.50,
        "p": 1.0,
        "tr": ["onOpponentEvade"],
        "trs": "self:buff=elita_counter_pouch_buff",
        "uit": ["none"],
        "a": [appr_weaken["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "ta": "opponent",
        "mt": "debuff",
        "s": "none",
        "st": 1,
    }

    # =========================================================================
    # 6. [被动] 关节狙击 (Joint Aim)
    #    - 远程攻击 100% 护甲穿透
    #    - 远程攻击命中或被防 70% 刷新对手减益持续时间
    # =========================================================================
    appr_aim = make_statmod_appearance(
        appr_id="appr_elita_joint_aim",
        callout_text="关节狙击",
        desc="远程攻击 100% 护甲穿透",
        pua_icon="\uE409",
        color=AbilityColor.ORANGE_DAMAGE,
        short_desc="关节狙击",
    )
    appears[appr_aim["id"]] = appr_aim
    mods["elita_joint_aim_pierce"] = {
        "id": "elita_joint_aim_pierce",
        "AppearanceID": appr_aim["id"],
        "Type": "combat",
        "t": "mod_armor_pierce",
        "d": 0.0,
        "m": 1.0,
        "p": 1.0,
        "tr": ["always"],
        "trs": "level=Ranged",
        "uit": ["none"],
        "a": [appr_aim["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "ta": "self",
        "mt": "passive",
        "s": "none",
    }

    appr_refresh = make_statmod_appearance(
        appr_id="appr_elita_joint_refresh",
        callout_text="减益刷新",
        desc="刷新对手身上的全部减益持续时间",
        pua_icon="\uE409",
        color=AbilityColor.RED_DEBUFF,
        short_desc="减益刷新",
    )
    appears[appr_refresh["id"]] = appr_refresh
    mods["elita_joint_aim_refresh"] = {
        "id": "elita_joint_aim_refresh",
        "AppearanceID": appr_refresh["id"],
        "Type": "combat",
        "t": "refresh_debuffs",
        "d": 0.0,
        "m": 1.0,
        "p": 0.70,
        "tr": ["onHit", "onBlocked"],
        "trs": "level=Ranged",
        "uit": ["none"],
        "a": [appr_refresh["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "ta": "opponent",
        "mt": "debuff",
        "s": "none",
    }

    # =========================================================================
    # 7. [被动] 远程暴击破甲 (Armor Break on Ranged Crit)
    #    - 远程暴击命中施加 50% 破甲持续 6 秒，最大叠加 1 层
    # =========================================================================
    m_rc_ab, a_rc_ab = make_armor_break_statmod(
        mod_id="elita_ranged_crit_armor_break",
        duration=6.0,
        break_amount=0.50,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Ranged",
        appr_id="appr_elita_rc_ab",
        callout_text="破甲",
        pua_icon="\uE516",
        color_hex=AbilityColor.RED_DEBUFF_TC,
        gradient_bottom=AbilityColor.RED_DEBUFF_GB,
        stackable=False,
        max_stacks=1,
    )
    mods.update(m_rc_ab)
    appears.update(a_rc_ab)

    # =========================================================================
    # 8. [被动] 领袖威仪 (Commander's Presence)
    #    - 受到 DOT 伤害期间每次命中对手加速 DOT 倒计时 20%
    # =========================================================================
    appr_presence = make_statmod_appearance(
        appr_id="appr_elita_presence",
        callout_text="领袖威仪",
        desc="受到 DOT 伤害时每次命中对手加速 DOT 倒计时 20%",
        pua_icon="\uE41F",
        color=AbilityColor.WHITE_SPECIAL,
        short_desc="领袖威仪",
    )
    appears[appr_presence["id"]] = appr_presence
    mods["elita_commanders_presence"] = {
        "id": "elita_commanders_presence",
        "AppearanceID": appr_presence["id"],
        "Type": "combat",
        "t": "accelerate_dot",
        "d": 0.0,
        "m": 0.20,
        "p": 1.0,
        "tr": ["onHit"],
        "trs": "self:has_dot=true",
        "uit": ["none"],
        "a": [appr_presence["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "ta": "self",
        "mt": "passive",
        "s": "none",
    }

    # =========================================================================
    # 9. [觉醒技] 抵抗军之火 (Resistance Flame)
    #    a) 生命低于 50%: 50% 攻击增益 + 50% 暴击率增益，持续 6 秒
    #    b) 生命低于 25%: 90% 护甲增益，持续 6 秒
    #    c) 生命低于 25%: 对手释放 SP1/SP2 40% 几率 (对斗士 70%) 打断并眩晕 1.5 秒
    # =========================================================================
    m_flame_atk, a_flame_atk = make_attack_boost_statmod(
        mod_id="elita_sig_flame_atk_50",
        duration=6.0,
        attack_bonus=0.50,
        chance=1.0,
        trigger="onHealthThreshold",
        trigger_scope="threshold=0.50",
        appr_id="appr_elita_flame_atk",
        callout_text="抵抗军之火",
        pua_icon="\uE942",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=False,
    )
    mods.update(m_flame_atk)
    appears.update(a_flame_atk)

    m_flame_crt, a_flame_crt = make_crit_rate_statmod(
        mod_id="elita_sig_flame_crit_50",
        duration=6.0,
        crit_bonus=0.50,
        chance=1.0,
        trigger="onHealthThreshold",
        trigger_scope="threshold=0.50",
        appr_id="appr_elita_flame_crt",
        callout_text="暴击强化",
        pua_icon="\uE942",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_flame_crt)
    appears.update(a_flame_crt)

    m_flame_arm, a_flame_arm = make_armor_up_statmod(
        mod_id="elita_sig_flame_armor_25",
        duration=6.0,
        armor_bonus=0.90,
        chance=1.0,
        trigger="onHealthThreshold",
        trigger_scope="threshold=0.25",
        appr_id="appr_elita_flame_arm",
        callout_text="绝境装甲",
        pua_icon="\uE942",
        color_hex=AbilityColor.BLUE_DEFENSE_TC,
        gradient_bottom=AbilityColor.BLUE_DEFENSE_GB,
        stackable=False,
    )
    mods.update(m_flame_arm)
    appears.update(a_flame_arm)

    m_flame_stn, a_flame_stn = make_stun_statmod(
        mod_id="elita_sig_flame_interrupt_stun",
        duration=1.5,
        chance=0.40,
        trigger="onOpponentSpecial",
        trigger_scope="self:hp<=0.25;level=Special1,Special2;once_per_fight=true",
        appr_id="appr_elita_flame_stn",
        callout_text="时空打断",
        pua_icon="\uE942",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m_flame_stn)
    appears.update(a_flame_stn)

    m_flame_braw, a_flame_braw = make_stun_statmod(
        mod_id="elita_sig_flame_interrupt_stun_braw",
        duration=1.5,
        chance=0.30,
        trigger="onOpponentSpecial",
        trigger_scope="self:hp<=0.25;level=Special1,Special2;opponent:class=braw;once_per_fight=true",
        appr_id="appr_elita_flame_braw",
        callout_text="战术反制",
        pua_icon="\uE942",
        color_hex=AbilityColor.YELLOW_STATUS_TC,
        gradient_bottom=AbilityColor.YELLOW_STATUS_GB,
    )
    mods.update(m_flame_braw)
    appears.update(a_flame_braw)

    # =========================================================================
    # 10. [协同] 永恒誓言 & 抵抗军姐妹
    # =========================================================================
    appr_bond = make_statmod_appearance(
        appr_id="appr_elita_bond_shield",
        callout_text="永恒誓言",
        desc="与擎天柱协同：战斗开局获得 15% 最大生命值护盾",
        pua_icon="\uE815",
        color=AbilityColor.BLUE_DEFENSE,
        short_desc="永恒誓言",
    )
    appears[appr_bond["id"]] = appr_bond
    mods["elita_synergy_eternal_bond_shield"] = {
        "id": "elita_synergy_eternal_bond_shield",
        "AppearanceID": appr_bond["id"],
        "Type": "combat",
        "t": "mod_shield",
        "d": 0.0,
        "m": float(round(base_hp * 0.15)),
        "p": 1.0,
        "tr": ["onCombatStart"],
        "trs": "",
        "uit": ["none"],
        "a": [appr_bond["id"]],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
        "ta": "self",
        "mt": "buff",
        "s": "none",
    }

    m_sis_crt, a_sis_crt = make_crit_rate_statmod(
        mod_id="elita_synergy_sisters_crit",
        duration=0.0,
        crit_bonus=0.10,
        chance=1.0,
        trigger="always",
        appr_id="appr_elita_sis_crt",
        callout_text="抵抗军姐妹",
        pua_icon="\uE40D",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
    )
    mods.update(m_sis_crt)
    appears.update(a_sis_crt)

    m_sis_hvy, a_sis_hvy = make_attack_boost_statmod(
        mod_id="elita_synergy_sisters_heavy",
        duration=0.0,
        attack_bonus=0.25,
        chance=1.0,
        trigger="always",
        trigger_scope="level=Heavy",
        appr_id="appr_elita_sis_hvy",
        callout_text="重击强化",
        pua_icon="\uE40D",
        color_hex=AbilityColor.ORANGE_DAMAGE_TC,
        gradient_bottom=AbilityColor.ORANGE_DAMAGE_GB,
        stackable=False,
    )
    mods.update(m_sis_hvy)
    appears.update(a_sis_hvy)

    # 校验所有产物符合 IL2CPP 底层契约
    for m in mods.values():
        validate_statmod(m)
    for a in appears.values():
        validate_appear(a)

    return mods, appears, buffs


@register_bot(
    BOT_ID,
    name_zh="艾丽塔",
    desc="汽车人抵抗军女领袖，战术系精锐。战术洞察规避霸体、灵动反击锦囊控场、远程穿甲刷新减益、SP破甲驱散震击与抵抗军之火绝境强化",
)
def build_elita_abilities(
    base_hp: float = 38400.0,
    base_atk: float = 2780.0,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    return _build_elita_abilities_impl(base_hp, base_atk)


@register_bot(
    BOT_ID_ALIAS,
    name_zh="艾丽塔",
    desc="汽车人抵抗军女领袖，战术系精锐 (Kabam 别名)",
)
def build_elita_abilities_alias(
    base_hp: float = 38400.0,
    base_atk: float = 2780.0,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    return _build_elita_abilities_impl(base_hp, base_atk)
