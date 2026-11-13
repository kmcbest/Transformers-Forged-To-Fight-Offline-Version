#!/usr/bin/env python3
"""
Bot Ability Implementation: 恐龙勇士 (Dinobot BW)
=================================================
Bot ID: dinobot_bw_kabam
阵营: 巨无霸 (Maximal) | 职业: 战术系 (Tactician)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 护甲穿透] (ID: 2501, pua_icon: 0xe409, category: passive)
   - 官方描述: "近战攻击自带65%的护甲穿透属性；近战暴击100%护甲穿透。"
   - 实现方案:
     a) dinobot_armor_pierce_melee: 近战攻击自带 65% 护甲穿透 (level=Light,Medium,Heavy)。
     b) dinobot_armor_pierce_crit: 近战暴击 100% 护甲穿透 (level=Light,Medium,Heavy;onCrit)。

2. [被动 - 格挡反伤] (ID: 2502, pua_icon: 0xe50f, category: passive)
   - 官方描述: "格挡对方近战攻击时，有60%的概率反向造成相当于对手攻击力10%的伤害，如果格挡对方的前冲攻击，概率为100%，伤害变为20%。"
   - 实现方案:
     由 skill_dinobot.c 接管底层格挡命中，判定近战/前冲攻击并造成反弹直伤。

3. [被动 - 格挡破甲] (ID: 2503, pua_icon: 0xe516, category: passive)
   - 官方描述: "格挡对方的前冲攻击，100%的概率施加1层40%的破甲减益，持续9秒。//如果对方身上有护甲，先抵消1层护甲。"
   - 实现方案:
     c) dinobot_dash_block_break: 触发 onBlock, 限制 opp.action=Dash，施加 1 层 40% 破甲 9 秒。

4. [被动 - 即时格挡精通] (ID: 2504, pua_icon: 0xe501, category: passive)
   - 官方描述: "即时格挡时增加50%的格挡精通 //降低格挡伤害50%，即时格挡判定条件同天火招架护盾 (held_ms <= 400ms)"
   - 实现方案:
     由 skill_dinobot.c 在格挡生效时检测即时格挡窗口，直接提升 50% 格挡减伤。

5. [被动 - 重击流血] (ID: 2505, pua_icon: 0xe401, category: passive)
   - 官方描述: "重击命中并出暴击时：100%几率触发流血，造成攻击力80%的伤害，持续5秒。"
   - 实现方案:
     d) dinobot_heavy_crit_bleed: 触发 onCrit, level=Heavy, 100% 概率施加 5.0 秒流血 debuff (80% base_atk 伤害)。呼出文字: "流血"。

6. [特殊技 1 - 破甲] (ID: 2506, pua_icon: 0xe516, category: special_1)
   - 官方描述: "每1击有80%的概率施加1层30%的破甲减益，持续8秒。//如果对方身上有护甲，先抵消1层护甲。"
   - 实现方案:
     e) dinobot_sp1_armor_break: 触发 onHit, level=Special1, 80% 概率施加 1 层 30% 破甲持续 8.0 秒。

7. [特殊技 2 - 暴击几率] (ID: 2507, pua_icon: 0xe40d, category: special_2)
   - 官方描述: "发动时，得到30%的暴击几率增益，持续9秒。"
   - 实现方案:
     f) dinobot_sp2_crit_rate: 触发 onSpecial2, 赋予自身 30% 暴击几率增益持续 9.0 秒。

8. [特殊技 3 - 修复与暴击几率] (ID: 2508, pua_icon: 0xe503/0xe40d, category: special_3)
   - 官方描述: "除第一击和最后一击外，每次攻击有50%的概率得到1层修复，4秒内修复最大生命值的3%；发动时得到30%暴击几率增益持续16秒。"
   - 实现方案:
     g) dinobot_sp3_crit_rate: 触发 onSpecial3, 赋予自身 30% 暴击几率增益持续 16.0 秒。
     h) dinobot_sp3_repair: 触发 onHit, level=Special3, 50% 几率在 4.0 秒内修复最大生命值的 3.0%。

9. [觉醒 - 适者生存] (ID: 2509, pua_icon: 0xe41f, category: signature)
   - 官方描述: "如果对手在破甲状态下格挡恐龙勇士的任何攻击，格挡伤害提高20%，并且恐龙勇士的攻击有20%的概率不可防御。"
   - 实现方案:
     由 skill_dinobot.c 针对破甲状态下的防御对手注入 20% 格挡穿透增伤与 20% 破防判定。
-----------------------------------------------------------------------------
"""

from ..core import (
    AbilityColor,
    make_bleed_statmod,
    make_armor_break_statmod,
    make_crit_rate_statmod,
    make_heal_statmod,
    make_statmod_appearance,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "dinobot_bw_kabam"


@register_bot(BOT_ID, name_zh="恐龙勇士", desc="战术系刀客，护甲穿透、格挡反伤破甲与暴击流血")
def build_dinobot_abilities(base_hp: float = 40154.0, base_atk: float = 3157.0):
    mods = {}
    appears = {}
    buffs = {}

    # -------------------------------------------------------------------------
    # 1. 护甲穿透被动 (近战 65% 护甲穿透，暴击 100% 护甲穿透)
    # -------------------------------------------------------------------------
    appr_pierce = make_statmod_appearance(
        appr_id="appr_dinobot_armor_pierce",
        callout_text="护甲穿透",
        desc="近战攻击具有护甲穿透效果，无视对手部分装甲减伤。",
        short_desc="护甲穿透",
        pua_icon="\uE409",
        color=AbilityColor.YELLOW_STATUS,
    )
    mod_pierce_melee = {
        "id": "dinobot_armor_pierce_melee",
        "t": "armor_pierce",
        "tm": "",
        "tr": ["onHit"],
        "uit": ["onHit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light,Medium,Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 0.65,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "armor_pierce",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dinobot_armor_pierce"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_pierce_melee)
    mods["dinobot_armor_pierce_melee"] = mod_pierce_melee

    mod_pierce_crit = {
        "id": "dinobot_armor_pierce_crit",
        "t": "armor_pierce",
        "tm": "",
        "tr": ["onCrit"],
        "uit": ["onCrit"],
        "pri": 0,
        "trm": 0.0,
        "trs": "level=Light,Medium,Heavy",
        "trr": "repeat",
        "c": 1.0,
        "m": 1.00,
        "d": -1.0,
        "s": "none",
        "ta": "self",
        "mt": "passive",
        "v": "",
        "ms": "",
        "st": 1,
        "g": "armor_pierce",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_dinobot_armor_pierce"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_pierce_crit)
    mods["dinobot_armor_pierce_crit"] = mod_pierce_crit
    appears["appr_dinobot_armor_pierce"] = appr_pierce

    # -------------------------------------------------------------------------
    # 2. 格挡前冲 100% 破甲 40% 持续 9 秒
    # -------------------------------------------------------------------------
    m_block_break, a_block_break = make_armor_break_statmod(
        mod_id="dinobot_dash_block_break",
        duration=9.0,
        break_amount=0.40,
        chance=1.0,
        trigger="onBlock",
        trigger_scope="opp.action=Dash",
        appr_id="appr_dinobot_dash_block_break",
        callout_text="破甲",
    )
    mods.update(m_block_break)
    appears.update(a_block_break)

    # -------------------------------------------------------------------------
    # 3. 重击暴击流血 (80% ATK 持续 5 秒, 100% 必发)
    # -------------------------------------------------------------------------
    m_heavy_bleed, a_heavy_bleed = make_bleed_statmod(
        mod_id="dinobot_heavy_crit_bleed",
        duration=5.0,
        total_dmg=float(round(base_atk * 0.80, 2)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Heavy",
        appr_id="appr_dinobot_bleed",
        callout_text="流血",
        buff_id="dmg_bleed",
    )
    mods.update(m_heavy_bleed)
    appears.update(a_heavy_bleed)

    # -------------------------------------------------------------------------
    # 4. SP1 每击 80% 破甲 30% 持续 8 秒
    # -------------------------------------------------------------------------
    m_sp1_break, a_sp1_break = make_armor_break_statmod(
        mod_id="dinobot_sp1_armor_break",
        duration=8.0,
        break_amount=0.30,
        chance=0.80,
        trigger="onHit",
        trigger_scope="level=Special1",
        appr_id="appr_dinobot_sp1_break",
        callout_text="破甲",
    )
    mods.update(m_sp1_break)
    appears.update(a_sp1_break)

    # -------------------------------------------------------------------------
    # 5. SP2 发动获得 30% 暴击几率 9 秒
    # -------------------------------------------------------------------------
    m_sp2_crit, a_sp2_crit = make_crit_rate_statmod(
        mod_id="dinobot_sp2_crit_rate",
        duration=9.0,
        crit_bonus=0.30,
        chance=1.0,
        trigger="onSpecial2",
        trigger_scope="level=Special2",
        appr_id="appr_dinobot_sp2_crit",
        callout_text="暴击几率",
    )
    mods.update(m_sp2_crit)
    appears.update(a_sp2_crit)

    # -------------------------------------------------------------------------
    # 6. SP3 发动获得 30% 暴击几率 16 秒
    # -------------------------------------------------------------------------
    m_sp3_crit, a_sp3_crit = make_crit_rate_statmod(
        mod_id="dinobot_sp3_crit_rate",
        duration=16.0,
        crit_bonus=0.30,
        chance=1.0,
        trigger="onSpecial3",
        trigger_scope="level=Special3",
        appr_id="appr_dinobot_sp3_crit",
        callout_text="暴击几率",
    )
    mods.update(m_sp3_crit)
    appears.update(a_sp3_crit)

    # -------------------------------------------------------------------------
    # 7. SP3 每次命中 50% 获得 4 秒 3% 最大生命值修复 (跳过首击和末击)
    # -------------------------------------------------------------------------
    heal_amount = float(round(base_hp * 0.03, 2))
    m_sp3_rep, a_sp3_rep = make_heal_statmod(
        mod_id="dinobot_sp3_repair",
        duration=4.0,
        heal_amount=heal_amount,
        chance=0.50,
        trigger="onHit",
        trigger_scope="level=Special3",
        appr_id="appr_dinobot_sp3_repair",
        callout_text="修复",
        buff_id="heal",
    )
    mods.update(m_sp3_rep)
    appears.update(a_sp3_rep)

    return mods, appears, buffs
