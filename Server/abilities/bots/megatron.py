#!/usr/bin/env python3
"""
Bot Ability Implementation: 威震天 (Megatron Leader)
======================================================
Bot ID: megatron_gs_leader2015
阵营: 霸天虎 (Decepticon) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 Upstash KV 聚合 Priorities 清单)】：
-----------------------------------------------------------------------------
1. [被动 - 融合炮] (ID: 3121, pua_icon: 0xe910)
   - 融合炮：每6秒充满一层融合炮，最多三层。拥有融合炮时重击飞行速度+50%。
   - 先灰色图标+6秒倒计时，充满一层后显示紫色同样图标，带数字表示层数。
2. [SP2 - 攻击减益] (ID: 3129, pua_icon: 0xe916)
   - 100%的概率施加44%的攻击减益，持续10秒。
3. [SP3 - 震击与过载] (ID: 3130, pua_icon: 0xe914)
   - 100%的概率施加造成攻击力300%伤害的震击，持续20秒。融合炮过载，本局可无限使用，不消耗。
4. [SP1 - 破甲] (ID: 3137, pua_icon: 0xe516)
   - 100%的概率施加38%的破甲，持续10秒。
5. [被动 - 减益融合] (ID: 3138, pua_icon: 0xe60f)
   - 重击击中对方时，如果对方身上有带倒计时的减益，将该减益变为无倒计时永久状态。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    make_armor_break_statmod,
    make_shock_statmod,
    validate_color_code,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "megatron_gs_leader2015"


@register_bot(BOT_ID, name_zh="威震天", desc="霸天虎统帅，融合炮自动蓄能，重击永久固化减益，SP1高额破甲与SP3雷霆震击")
def build_megatron_abilities(base_hp: float = 31000.0, base_atk: float = 2450.0):
    mods = {}
    appears = {}

    # 1a. 融合炮充能倒计时 (6秒灰色倒计时图标 \uE910，开局立即触发)
    appr_fusion_cd = make_statmod_appearance(
        appr_id="appr_megatron_fusion_cd",
        desc="每6秒充能一层融合炮",
        short_desc="融合炮充能中",
        pua_icon="\uE910",
        color=AbilityColor.GRAY_COOLDOWN,
        show_callout=False,
        active_desc="融合炮充能中",
    )
    mod_fusion_cd = {
        "id": "megatron_fusion_cd",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onStart"],
        "uit": ["onStart"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": 6.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "fusion_cannon_cd",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_fusion_cd"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_fusion_cd)
    mods["megatron_fusion_cd"] = mod_fusion_cd
    appears["appr_megatron_fusion_cd"] = appr_fusion_cd

    # 1b. 融合炮充能层数 (ID: 3121): 充满后显示深紫色图标，带数字表示层数 (上限 3 层，常驻 d=-1.0)
    appr_fusion = make_statmod_appearance(
        appr_id="appr_megatron_fusion_cannon",
        callout_text="融合炮",
        desc="每6秒充能一层融合炮(上限3层)，重击飞行速度+50%",
        short_desc="融合炮充能",
        pua_icon="\uE910",
        color=AbilityColor.DARK_PURPLE_SPECIAL,
        show_callout=True,
        active_desc="融合炮已就绪",
    )
    mod_fusion = {
        "id": "megatron_fusion_cannon",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onStart"],
        "uit": ["onStart"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.0,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 3,
        "g": "fusion_cannon",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_fusion_cannon"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_fusion)
    mods["megatron_fusion_cannon"] = mod_fusion
    appears["appr_megatron_fusion_cannon"] = appr_fusion

    # 2. SP2 攻击减益 (ID: 3129): 100% 施加 44% 攻击减益 10 秒
    appr_sp2_atk = make_statmod_appearance(
        appr_id="appr_megatron_sp2_atk_debuff",
        callout_text="虚弱",
        desc="降低对手44%的攻击力",
        short_desc="攻击力削弱",
        pua_icon="\uE916",
        color=AbilityColor.RED_DEBUFF,
        show_callout=True,
        active_desc="攻击减益生效中",
    )
    mod_sp2_atk = {
        "id": "megatron_sp2_atk_debuff",
        "t": "attack_debuff",
        "tm": "",
        "tr": ["onSpecial2Activate"],
        "uit": ["onSpecial2Activate"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.44,
        "d": 10.0,
        "s": "none",
        "ta": "opponent",
        "mt": "debuff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "attack_debuff",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_sp2_atk_debuff"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_sp2_atk)
    mods["megatron_sp2_atk_debuff"] = mod_sp2_atk
    appears["appr_megatron_sp2_atk_debuff"] = appr_sp2_atk

    # 3. SP3 震击与过载 (ID: 3130): 100% 施加 300% 震击 20s
    m_sp3_s, a_sp3_s = make_shock_statmod(
        mod_id="megatron_sp3_shock",
        duration=20.0,
        total_dmg=float(round(base_atk * 3.00)),
        chance=1.0,
        trigger="onSpecial3Activate",
        appr_id="appr_megatron_sp3_shock",
        callout_text="震击",
        show_callout=True,
        pua_icon="\uE914",
    )
    mods.update(m_sp3_s)
    appears.update(a_sp3_s)

    # 4. SP1 破甲 (ID: 3137): 100% 施加 38% 破甲 10 秒
    m_sp1_ab, a_sp1_ab = make_armor_break_statmod(
        mod_id="megatron_sp1_armor_break",
        duration=10.0,
        break_amount=0.38,
        chance=1.0,
        trigger="onSpecial1Activate",
        appr_id="appr_megatron_sp1_armor_break",
        callout_text="破甲",
        show_callout=True,
        pua_icon="\uE516",
    )
    mods.update(m_sp1_ab)
    appears.update(a_sp1_ab)

    # 5. 被动减益融合 (ID: 3138): 拥有融合炮重击命中时，将对方身上的限时减益永久化锁定，此时才呼出显示“减益融合”
    appr_fusion_deb = make_statmod_appearance(
        appr_id="appr_megatron_debuff_fusion",
        callout_text="减益融合",
        desc="重击命中将目标身上的限时减益永久化锁定",
        short_desc="减益永久锁定",
        pua_icon="\uE60F",
        color=AbilityColor.LIGHT_PURPLE_POWER,
        show_callout=True,
        active_desc="减益融合生效中",
    )
    mod_fusion_deb = {
        "id": "megatron_debuff_fusion",
        "t": "buff",
        "tm": "",
        "tr": ["onStart"],           # 开局由 hook_192 捕获指针并抑制激活，仅在重击成功融合减益时触发弹字
        "uit": ["onStart"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.0,
        "d": 1.5,                    # 短暂弹字与呼出大字提示
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "debuff_fusion_callout",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_debuff_fusion"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_fusion_deb)
    mods["megatron_debuff_fusion"] = mod_fusion_deb
    appears["appr_megatron_debuff_fusion"] = appr_fusion_deb

    # 6. SP3 融合炮过载 (ID: 3130b): 图标变为绿色 \uE910，不带数字，本局无限使用不消耗
    appr_overload = make_statmod_appearance(
        appr_id="appr_megatron_fusion_overload",
        callout_text="融合炮过载",
        desc="融合炮过载，无限全功率重击且不消耗融合炮层数",
        short_desc="融合炮过载",
        pua_icon="\uE910",
        color=AbilityColor.GREEN_HEALTH,
        show_callout=True,
        active_desc="融合炮过载生效中",
    )
    mod_overload = {
        "id": "megatron_fusion_overload",
        "t": "attack_buff",
        "tm": "",
        "tr": ["onStart"],           # 开局由 hook_192 捕获指针并抑制激活，SP3 施放时显现
        "uit": ["onStart"],
        "pri": 0,
        "trm": 0.0,
        "trs": "",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.30,
        "d": -1.0,                   # 本局永久常驻
        "s": "none",
        "ta": "self",
        "mt": "buff",
        "v": "",
        "ms": "",
        "st": 1,                     # 不带数字
        "g": "fusion_cannon",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_megatron_fusion_overload"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_overload)
    mods["megatron_fusion_overload"] = mod_overload
    appears["appr_megatron_fusion_overload"] = appr_overload

    return mods, appears
