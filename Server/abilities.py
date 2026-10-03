#!/usr/bin/env python3
"""
TFTF Combat Ability & Buff System (战斗能力与 Buff 系统配置模块)
================================================================

本模块为 Transformers Forged To Fight 离线版战斗能力系统的【独立单一真理源】。
负责定义：
  1. 全局 Buff 行为定义 (buffs_set / globalBuffs)
  2. UI 分组与堆叠策略 (buffs_config / groupings)
  3. 技能外观表现与 PUA 字体图标 (statModAppears)
  4. 战斗修饰器与触发逻辑 (statMods)
  5. 角色与技能的绑定关系 (bot_abilities)

----------------------------------------------------------------
【底层 IL2CPP 契约与逆向铁律 (必读)】：
  1. 数值 m (Magnitude) 是持续时间 d 内的【绝对总伤害数值】，绝非攻击力百分比！
     - 伤害 Tick 公式：per_tick = m / (d * 2.0) （每 0.5s Tick 一次，总共 2*d 次）
     - 因客户端跳字强转整型 int，若 m <= 2*d 会截断为 0，导致静默无伤害无跳字。
  2. 颜色代码 (tc, gt, gb) 必须使用【纯 6 位十六进制字符串】（如 "FF0000"），严禁加 "#"！
     - 底层 HexToColor (0x18AF58C) 从 index 0 开始两两读取，"#" 会被 0x18AB274 解析为 0xF，
       导致 "#FF0000" 移位错位解析为 RGB(255, 240, 0) 亮黄色！
  3. 列表访问器类型安全：tr、uit、a 字段在底层均为 C# List，必须传入 Python 数组 (如 ["onHit"])。
  4. PUA 字体图标：Tecnica_Bold_116.ttf 矢量字体，\uE401 为流血能量块滴液图标。
----------------------------------------------------------------
"""

import os

# ---------------------------------------------------------------------------
# 1. Buff UI 分组与显示配置 (buffs_config)
# ---------------------------------------------------------------------------
def build_buffs_config():
    """定义战斗中各类 Buff 的堆叠与血条下 UI 挂件显示策略。"""
    groups_data = {
        # 跳字累加器：常驻不可见
        "floating_text": {"stackable": True, "active_display": False},
        "floating_text_dmg": {"stackable": True, "active_display": False},
        "floating_text_heal": {"stackable": True, "active_display": False},
        # SP 技能呼出文字组：仅触发 Callout Text，不在血条下显示 Buff 图标
        "sp_callout": {"stackable": True, "active_display": False},
        # 流血类 Debuff：可堆叠，在敌人血条下方显示倒计时圆环图标
        "dmg_bleed": {"stackable": True, "active_display": True},
        # 直接伤害：不显示血条下方图标
        "dmg_direct": {"stackable": True, "active_display": False},
    }
    return {
        # 客户端 BuffsConfig.<groups>k__BackingField 期望字段名为 groups
        "groups": groups_data,
        "groupings": groups_data,
    }


# ---------------------------------------------------------------------------
# 2. 全局 Buff 引擎行为 (buffs_set)
# ---------------------------------------------------------------------------
def build_buffs_set():
    """全局 Buff 模板库。每个 id 对应 Damage_BuffEffect 或 FloatingText_BuffEffect。"""
    return {
        "globalBuffs": {
            # 通用 SP 技能呼出 Buff：触发时向对应角色侧派发 1 秒技能名 Callout
            "sp_callout": {
                "id": "sp_callout",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 0.0,
                "c": 1,
                "value": 0.0,
                "buffType": "buff",
                "group": "sp_callout",
                "p": {},
                "hasDuration": True,
                "e": 0,
                "time": {"amount": 1.0},
                "loc_name": "sp_callout",
                "loc_desc": "sp_callout",
            },
            # 伤害跳字收集器：捕获 _ftd 变量累加值，弹出红色跳字 (style 7)
            "floating_text": {
                "id": "floating_text",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 0.0,
                "c": 1,
                "value": 0.0,
                "buffType": "floating_text",
                "group": "floating_text",
                "p": {"key": "_ftd", "style": 0},
                "hasDuration": False,
                "e": 0,
                "time": {"amount": 0},
                "loc_name": "floating_text",
                "loc_desc": "floating_text",
            },
            # 治疗跳字收集器：捕获 _fth 变量累加值，弹出绿色跳字 (style 6)
            "floating_text_heal": {
                "id": "floating_text_heal",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 0.0,
                "c": 1,
                "value": 0.0,
                "buffType": "floating_text",
                "group": "floating_text_heal",
                "p": {"key": "_fth", "style": 0},
                "hasDuration": False,
                "e": 0,
                "time": {"amount": 0},
                "loc_name": "floating_text_heal",
                "loc_desc": "floating_text_heal",
            },
            # 阿尔茜普通爆头即时直接伤害 (Direct instant damage)
            "dmg_direct": {
                "id": "dmg_direct",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 2091.0,
                "c": 1,
                "value": 2091.0,
                "buffType": "damage",
                "group": "dmg_direct",
                "p": {"damage_type": "bleed"},
                "hasDuration": True,
                "e": 0,
                "time": {"amount": 0.5},
                "loc_name": "headshot_direct",
                "loc_desc": "headshot_direct",
            },
            # 阿尔茜爆头流血 3 秒 DOT (3.0s Bleed DOT)
            "dmg_bleed": {
                "id": "dmg_bleed",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 2091.0,
                "c": 1,
                "value": 2091.0,
                "buffType": "damage",
                "group": "dmg_bleed",
                "p": {"damage_type": "bleed"},
                "hasDuration": True,
                "e": 0,
                "time": {"amount": 3.0},
                "loc_name": "bleed",
                "loc_desc": "bleed",
            },
            # 阿尔茜 S2 暴击流血 4 秒 DOT (4.0s Bleed DOT)
            "dmg_bleed_s2": {
                "id": "dmg_bleed_s2",
                "iconTexture": "",
                "image": "",
                "images3": False,
                "modeAvail": [],
                "scope": "global",
                "valueType": "absolute",
                "displayValue": 3764.0,
                "c": 1,
                "value": 3764.0,
                "buffType": "damage",
                "group": "dmg_bleed",
                "p": {"damage_type": "bleed"},
                "hasDuration": True,
                "e": 0,
                "time": {"amount": 4.0},
                "loc_name": "bleed",
                "loc_desc": "bleed",
            },
        },
        "userBuffs": {}
    }


# ---------------------------------------------------------------------------
# 3. 角色 SP 特殊技本地化映射表 (BOT_SP_MAP)
# ---------------------------------------------------------------------------
BOT_SP_MAP = {
    "acidstorm_gs_leader2015": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "arcee_gs_deluxe2014": ("ID_SPECIAL_ATTACK_ARCEE_GS_0", "ID_SPECIAL_ATTACK_ARCEE_GS_1", "ID_SPECIAL_ATTACK_ARCEE_GS_2"),
    "barricade_cin_dotm": ("ID_SPECIAL_ATTACK_BARRI_C_0", "ID_SPECIAL_ATTACK_BARRI_C_1", "ID_SPECIAL_ATTACK_BARRI_C_2"),
    "bitstream_gs_leader2015": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "blaster_gs_leader2016": ("ID_SPECIAL_ATTACK_BLASTR_GS_0", "ID_SPECIAL_ATTACK_BLASTR_GS_1", "ID_SPECIAL_ATTACK_BLASTR_GS_2"),
    "bludgeon_gs_rd20": ("ID_SPECIAL_ATTACK_BLUDGE_GS_0", "ID_SPECIAL_ATTACK_BLUDGE_GS_1", "ID_SPECIAL_ATTACK_BLUDGE_GS_2"),
    "bonecrusher_cin_rotf": ("ID_SPECIAL_ATTACK_BONEC_C_0", "ID_SPECIAL_ATTACK_BONEC_C_1", "ID_SPECIAL_ATTACK_BONEC_C_2"),
    "breakdown_gs": ("ID_SPECIAL_ATTACK_SIDES_GS_0", "ID_SPECIAL_ATTACK_SIDES_GS_1", "ID_SPECIAL_ATTACK_SIDES_GS_2"),
    "bumblebee_cin_dotm": ("ID_SPECIAL_ATTACK_BUMBL_C_0", "ID_SPECIAL_ATTACK_BUMBL_C_1", "ID_SPECIAL_ATTACK_BUMBL_C_2"),
    "bumblebee_gs_kabam": ("ID_SPECIAL_ATTACK_BUMBL_GS_0", "ID_SPECIAL_ATTACK_BUMBL_GS_1", "ID_SPECIAL_ATTACK_BUMBL_GS_2"),
    "cheetor_bw_transmetal": ("ID_SPECIAL_ATTACK_CHEETOR_BW_0", "ID_SPECIAL_ATTACK_CHEETOR_BW_1", "ID_SPECIAL_ATTACK_CHEETOR_BW_2"),
    "chromia_gs_kabam": ("ID_SPECIAL_ATTACK_ARCEE_GS_0", "ID_SPECIAL_ATTACK_ARCEE_GS_1", "ID_SPECIAL_ATTACK_ARCEE_GS_2"),
    "cliffjumper_gs_kabam": ("ID_SPECIAL_ATTACK_CLIFFJUMP_GS_0", "ID_SPECIAL_ATTACK_CLIFFJUMP_GS_1", "ID_SPECIAL_ATTACK_CLIFFJUMP_GS_2"),
    "cyclonus_gs_uw06": ("ID_SPECIAL_ATTACK_CYCLON_GS_0", "ID_SPECIAL_ATTACK_CYCLON_GS_1", "ID_SPECIAL_ATTACK_CYCLON_GS_2"),
    "deadend_gs_deluxe2015": ("ID_SPECIAL_ATTACK_MIRAG_GS_0", "ID_SPECIAL_ATTACK_MIRAG_GS_1", "ID_SPECIAL_ATTACK_MIRAG_GS_2"),
    "dinobot_bw_kabam": ("ID_SPECIAL_ATTACK_DINOB_BW_0", "ID_SPECIAL_ATTACK_DINOB_BW_1", "ID_SPECIAL_ATTACK_DINOB_BW_2"),
    "dirge_gs_deluxe2008": ("ID_SPECIAL_ATTACK_RAMJET_GS_0", "ID_SPECIAL_ATTACK_RAMJET_GS_1", "ID_SPECIAL_ATTACK_RAMJET_GS_2"),
    "dragstrip_gs_deluxe2016": ("ID_SPECIAL_ATTACK_MIRAG_GS_0", "ID_SPECIAL_ATTACK_MIRAG_GS_1", "ID_SPECIAL_ATTACK_MIRAG_GS_2"),
    "drift_cin_aoe": ("ID_SPECIAL_ATTACK_DRIFT_C_0", "ID_SPECIAL_ATTACK_DRIFT_C_1", "ID_SPECIAL_ATTACK_DRIFT_C_2"),
    "fte_optimus_gs_t3": ("ID_SPECIAL_ATTACK_OPTIMUS_GS_0", "ID_SPECIAL_ATTACK_OPTIMUS_GS_1", "ID_SPECIAL_ATTACK_OPTIMUS_GS_2"),
    "fte_stars_gs_t3": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "galvatron_gs_voyager2016": ("ID_SPECIAL_ATTACK_GALVATRON_GS_0", "ID_SPECIAL_ATTACK_GALVATRON_GS_1", "ID_SPECIAL_ATTACK_GALVATRON_GS_2"),
    "grimlock_gs_mp08": ("ID_SPECIAL_ATTACK_GRIML_GS_0", "ID_SPECIAL_ATTACK_GRIML_GS_1", "ID_SPECIAL_ATTACK_GRIML_GS_2"),
    "grindor_cin_rotf": ("ID_SPECIAL_ATTACK_GRIND_C_ROTF_0", "ID_SPECIAL_ATTACK_GRIND_C_ROTF_1", "ID_SPECIAL_ATTACK_GRIND_C_ROTF_2"),
    "hotlink_gs_leader2015": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "hotrod_cin_tlk": ("ID_SPECIAL_ATTACK_HOTRO_C_0", "ID_SPECIAL_ATTACK_HOTRO_C_1", "ID_SPECIAL_ATTACK_HOTRO_C_2"),
    "hound_cin_tlk": ("ID_SPECIAL_ATTACK_HOUND_C_0", "ID_SPECIAL_ATTACK_HOUND_C_1", "ID_SPECIAL_ATTACK_HOUND_C_2"),
    "ionstorm_gs_leader2015": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "ironhide_cin_rotf": ("ID_SPECIAL_ATTACK_IRONH_C_ROTF_0", "ID_SPECIAL_ATTACK_IRONH_C_ROTF_1", "ID_SPECIAL_ATTACK_IRONH_C_ROTF_2"),
    "ironhide_gs_kabam": ("ID_SPECIAL_ATTACK_IRONH_C_ROTF_0", "ID_SPECIAL_ATTACK_IRONH_C_ROTF_1", "ID_SPECIAL_ATTACK_IRONH_C_ROTF_2"),
    "jazz_gs_twm05": ("ID_SPECIAL_ATTACK_JAZZ_GS_0", "ID_SPECIAL_ATTACK_JAZZ_GS_1", "ID_SPECIAL_ATTACK_JAZZ_GS_2"),
    "jetfire_gs_leader2014": ("ID_SPECIAL_ATTACK_JETFIRE_GS_0", "ID_SPECIAL_ATTACK_JETFIRE_GS_1", "ID_SPECIAL_ATTACK_JETFIRE_GS_2"),
    "kickback_gs_kabam": ("ID_SPECIAL_ATTACK_KICKB_GS_0", "ID_SPECIAL_ATTACK_KICKB_GS_1", "ID_SPECIAL_ATTACK_KICKB_GS_2"),
    "lifeline_gs_deluxe2014": ("ID_SPECIAL_ATTACK_ARCEE_GS_0", "ID_SPECIAL_ATTACK_ARCEE_GS_1", "ID_SPECIAL_ATTACK_ARCEE_GS_2"),
    "megatron_cin_rotf": ("ID_SPECIAL_ATTACK_MEGAT_C_0", "ID_SPECIAL_ATTACK_MEGAT_C_1", "ID_SPECIAL_ATTACK_MEGAT_C_2"),
    "megatron_gs_leader2015": ("ID_SPECIAL_ATTACK_MEGAT_GS_0", "ID_SPECIAL_ATTACK_MEGAT_GS_1", "ID_SPECIAL_ATTACK_MEGAT_GS_2"),
    "megatronus_gs_kabam": ("ID_SPECIAL_ATTACK_MEGATRO_GS_0", "ID_SPECIAL_ATTACK_MEGATRO_GS_1", "ID_SPECIAL_ATTACK_MEGATRO_GS_2"),
    "mirage_gs_deluxe2016": ("ID_SPECIAL_ATTACK_MIRAG_GS_0", "ID_SPECIAL_ATTACK_MIRAG_GS_1", "ID_SPECIAL_ATTACK_MIRAG_GS_2"),
    "mixmaster_cin_rotf": ("ID_SPECIAL_ATTACK_MIXMA_C_ROTF_0", "ID_SPECIAL_ATTACK_MIXMA_C_ROTF_1", "ID_SPECIAL_ATTACK_MIXMA_C_ROTF_2"),
    "motormaster_gs_voyager2015": ("ID_SPECIAL_ATTACK_MOTORM_GS_0", "ID_SPECIAL_ATTACK_MOTORM_GS_1", "ID_SPECIAL_ATTACK_MOTORM_GS_2"),
    "necrotronus_gs_kabam": ("ID_SPECIAL_ATTACK_NECROTRO_GS_0", "ID_SPECIAL_ATTACK_NECROTRO_GS_1", "ID_SPECIAL_ATTACK_NECROTRO_GS_2"),
    "nemesisprime_gs_voyager2015": ("ID_SPECIAL_ATTACK_NEMESIS_GS_0", "ID_SPECIAL_ATTACK_NEMESIS_GS_1", "ID_SPECIAL_ATTACK_NEMESIS_GS_2"),
    "novastorm_gs_leader2015": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "optimusprimal_bw_mp32": ("ID_SPECIAL_ATTACK_OPRIMAL_BW_0", "ID_SPECIAL_ATTACK_OPRIMAL_BW_1", "ID_SPECIAL_ATTACK_OPRIMAL_BW_2"),
    "optimusprime_cin_tf": ("ID_SPECIAL_ATTACK_OPTIMUS_C_TF_0", "ID_SPECIAL_ATTACK_OPTIMUS_C_TF_1", "ID_SPECIAL_ATTACK_OPTIMUS_C_TF_2"),
    "optimusprime_sg_voyager2015": ("ID_SPECIAL_ATTACK_OPTIMUS_GS_0", "ID_SPECIAL_ATTACK_OPTIMUS_GS_1", "ID_SPECIAL_ATTACK_OPTIMUS_GS_2"),
    "prowl_gs_deluxe2016": ("ID_SPECIAL_ATTACK_PROWL_GS_0", "ID_SPECIAL_ATTACK_PROWL_GS_1", "ID_SPECIAL_ATTACK_PROWL_GS_2"),
    "ramjet_gs_deluxe2008": ("ID_SPECIAL_ATTACK_RAMJET_GS_0", "ID_SPECIAL_ATTACK_RAMJET_GS_1", "ID_SPECIAL_ATTACK_RAMJET_GS_2"),
    "ratchet_gs_kabam": ("ID_SPECIAL_ATTACK_RATCH_GS_0", "ID_SPECIAL_ATTACK_RATCH_GS_1", "ID_SPECIAL_ATTACK_RATCH_GS_2"),
    "rhinox_gs_voyager2014": ("ID_SPECIAL_ATTACK_RHINO_BW_0", "ID_SPECIAL_ATTACK_RHINO_BW_1", "ID_SPECIAL_ATTACK_RHINO_BW_2"),
    "rodimusprime_gs_mp09": ("ID_SPECIAL_ATTACK_HOTRO_C_0", "ID_SPECIAL_ATTACK_HOTRO_C_1", "ID_SPECIAL_ATTACK_HOTRO_C_2"),
    "scorponok_bw_kabam": ("ID_SPECIAL_ATTACK_SCORPO_BW_0", "ID_SPECIAL_ATTACK_SCORPO_BW_1", "ID_SPECIAL_ATTACK_SCORPO_BW_2"),
    "sharkticon_gs_brawler": ("ID_SPECIAL_ATTACK_NPC_SHARK_BRAW_0", "ID_SPECIAL_ATTACK_NPC_SHARK_BRAW_1", "ID_SPECIAL_ATTACK_NPC_SHARK_BRAW_2"),
    "sharkticon_gs_demolition": ("ID_SPECIAL_ATTACK_NPC_SHARK_DEMO_0", "ID_SPECIAL_ATTACK_NPC_SHARK_DEMO_1", "ID_SPECIAL_ATTACK_NPC_SHARK_DEMO_2"),
    "sharkticon_gs_kabam": ("ID_SPECIAL_ATTACK_NPC_SHARK_GOLD_0", "ID_SPECIAL_ATTACK_NPC_SHARK_GOLD_1", "ID_SPECIAL_ATTACK_NPC_SHARK_GOLD_2"),
    "sharkticon_gs_scout": ("ID_SPECIAL_ATTACK_NPC_SHARK_SCOU_0", "ID_SPECIAL_ATTACK_NPC_SHARK_SCOU_1", "ID_SPECIAL_ATTACK_NPC_SHARK_SCOU_2"),
    "sharkticon_gs_tactician": ("ID_SPECIAL_ATTACK_NPC_SHARK_TACT_0", "ID_SPECIAL_ATTACK_NPC_SHARK_TACT_1", "ID_SPECIAL_ATTACK_NPC_SHARK_TACT_2"),
    "sharkticon_gs_tech": ("ID_SPECIAL_ATTACK_NPC_SHARK_TECH_0", "ID_SPECIAL_ATTACK_NPC_SHARK_TECH_1", "ID_SPECIAL_ATTACK_NPC_SHARK_TECH_2"),
    "sharkticon_gs_warrior": ("ID_SPECIAL_ATTACK_NPC_SHARK_WARR_0", "ID_SPECIAL_ATTACK_NPC_SHARK_WARR_1", "ID_SPECIAL_ATTACK_NPC_SHARK_WARR_2"),
    "shockwave_gs": ("ID_SPECIAL_ATTACK_SHOCK_C_0", "ID_SPECIAL_ATTACK_SHOCK_C_1", "ID_SPECIAL_ATTACK_SHOCK_C_2"),
    "sideswipe_gs": ("ID_SPECIAL_ATTACK_SIDES_GS_0", "ID_SPECIAL_ATTACK_SIDES_GS_1", "ID_SPECIAL_ATTACK_SIDES_GS_2"),
    "skywarp_gs_leader2015": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "slipstream_gs": ("ID_SPECIAL_ATTACK_WINDB_GS_0", "ID_SPECIAL_ATTACK_WINDB_GS_1", "ID_SPECIAL_ATTACK_WINDB_GS_2"),
    "soundblaster_gs_mp13b": ("ID_SPECIAL_ATTACK_SOUND_GS_0", "ID_SPECIAL_ATTACK_SOUND_GS_1", "ID_SPECIAL_ATTACK_SOUND_GS_2"),
    "soundwave_gs": ("ID_SPECIAL_ATTACK_SOUND_GS_0", "ID_SPECIAL_ATTACK_SOUND_GS_1", "ID_SPECIAL_ATTACK_SOUND_GS_2"),
    "starsaber_gs_leader2014": ("ID_SPECIAL_ATTACK_DRIFT_C_0", "ID_SPECIAL_ATTACK_DRIFT_C_1", "ID_SPECIAL_ATTACK_DRIFT_C_2"),
    "starscream_ghost_gs": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "sunstorm_gs_leader2015": ("ID_SPECIAL_ATTACK_STARS_GS_0", "ID_SPECIAL_ATTACK_STARS_GS_1", "ID_SPECIAL_ATTACK_STARS_GS_2"),
    "sunstreaker_gs_deluxe2008": ("ID_SPECIAL_ATTACK_SIDES_GS_0", "ID_SPECIAL_ATTACK_SIDES_GS_1", "ID_SPECIAL_ATTACK_SIDES_GS_2"),
    "tantrum_gs_kabam": ("ID_SPECIAL_ATTACK_TANTRUM_GS_0", "ID_SPECIAL_ATTACK_TANTRUM_GS_1", "ID_SPECIAL_ATTACK_TANTRUM_GS_2"),
    "thrust_gs_deluxe2008": ("ID_SPECIAL_ATTACK_RAMJET_GS_0", "ID_SPECIAL_ATTACK_RAMJET_GS_1", "ID_SPECIAL_ATTACK_RAMJET_GS_2"),
    "thundercracker_gs_leader2015": ("ID_SPECIAL_ATTACK_THUNDERCRACKER_GS_0", "ID_SPECIAL_ATTACK_THUNDERCRACKER_GS_1", "ID_SPECIAL_ATTACK_THUNDERCRACKER_GS_2"),
    "ultramagnus_gs_leader": ("ID_SPECIAL_ATTACK_ULTRAM_GS_0", "ID_SPECIAL_ATTACK_ULTRAM_GS_1", "ID_SPECIAL_ATTACK_ULTRAM_GS_2"),
    "ultramagnus_sg_leader": ("ID_SPECIAL_ATTACK_ULTRAM_GS_0", "ID_SPECIAL_ATTACK_ULTRAM_GS_1", "ID_SPECIAL_ATTACK_ULTRAM_GS_2"),
    "waspinator_gs_deluxe": ("ID_SPECIAL_ATTACK_WASP_BW_0", "ID_SPECIAL_ATTACK_WASP_BW_1", "ID_SPECIAL_ATTACK_WASP_BW_2"),
    "wheeljack_gs_mp20": ("ID_SPECIAL_ATTACK_WHEELJ_GS_0", "ID_SPECIAL_ATTACK_WHEELJ_GS_1", "ID_SPECIAL_ATTACK_WHEELJ_GS_2"),
    "wildrider_gs_deluxe2016": ("ID_SPECIAL_ATTACK_SIDES_GS_0", "ID_SPECIAL_ATTACK_SIDES_GS_1", "ID_SPECIAL_ATTACK_SIDES_GS_2"),
    "windblade_gs": ("ID_SPECIAL_ATTACK_WINDB_GS_0", "ID_SPECIAL_ATTACK_WINDB_GS_1", "ID_SPECIAL_ATTACK_WINDB_GS_2"),
}


# ---------------------------------------------------------------------------
# 4. 视觉表现与图标映射 (statModAppears)
# ---------------------------------------------------------------------------
def build_stat_mod_appears():
    """定义修饰器的视觉效果、Unicode PUA 图标字形、呼出文字及纯 6 位 Hex 颜色。"""
    res = {
        # 阿尔茜爆头即时直接命中外观
        "appr_arcee_headshot": {
            "id": "appr_arcee_headshot",
            "a": "Headshot",
            "s": "Headshot",
            "l": "Direct headshot strike inflicts extra direct damage.",
            "ss": "Direct headshot damage.",
            "t": "\uE401",                # 能量块流血字形
            "f": "",
            "st": "HEADSHOT",             # 命中呼出大字
            "ps": "Headshot",
            "pl": "Direct headshot damage.",
            "tc": "FF0000",               # 纯 6 位 Hex：鲜红色 (严禁带 '#')
            "gt": "FF0000",
            "gb": "FF0000",
        },
        # 阿尔茜流血 DOT 持续伤害外观 (同时服务于普通远程暴击与S2暴击流血，统一字形与颜色以支持图标数字角标堆叠)
        "appr_arcee_bleed": {
            "id": "appr_arcee_bleed",
            "a": "Bleed",
            "s": "Bleed",
            "l": "Direct bleed damage ignoring armor over duration.",
            "ss": "Bleed damage over duration.",
            "t": "\uE401",                # 能量块流血字形（血条下方倒计时圆环图标）
            "f": "",
            "st": "BLEED",                # 命中呼出大字 BLEED
            "ps": "Bleed",
            "pl": "Bleed damage ignoring armor.",
            "tc": "FF0000",               # 纯正红色 (0xFF, 0x00, 0x00)
            "gt": "FF0000",
            "gb": "FF0000",
        },
    }

    # 为全员 78 位英雄注册 SP1 / SP2 / SP3 技能名呼出外观
    # 采用高亮金色 (FFE066) 配以纯白色高光渐变，呼出文字绑定官方多语言 ID
    for bid, sp_keys in BOT_SP_MAP.items():
        for lvl in (1, 2, 3):
            appr_id = f"appr_sp_{bid}_{lvl}"
            res[appr_id] = {
                "id": appr_id,
                "a": f"SP{lvl}",
                "s": f"SP{lvl}",
                "l": "",
                "ss": "",
                "t": "",
                "f": "",
                "st": sp_keys[lvl - 1],   # 客户端 UILabel 自动解析该语言键值
                "ps": "",
                "pl": "",
                "tc": "FFE066",           # 纯 6 位 Hex：辉光金
                "gt": "FFFFFF",           # 上部渐变高光纯白
                "gb": "FFAA00",           # 下部渐变深金
            }

    return res


# ---------------------------------------------------------------------------
# 4. 战斗修饰器与触发器定义 (statMods)
# ---------------------------------------------------------------------------
def build_stat_modifiers():
    """定义具体的触发条件、几率、持续时间与作用对象。"""
    res = {
        # -------------------------------------------------------------------
        # [全局系统修饰器]
        # -------------------------------------------------------------------
        # 受击硬直修饰器 (内置默认)
        "gp_hit_stun": {
            "id": "gp_hit_stun",
            "t": "hit_stun",
            "tm": "",
            "tr": [],
            "uit": [],
            "pri": 0,
            "trm": 0.0,
            "trs": "",
            "trr": "none",
            "c": 1.0,
            "m": 1.0,
            "d": 0.5,
            "s": "none",
            "ta": "self",
            "mt": "debuff",
            "v": "",
            "ms": "",
            "st": 0,
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": [],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },
        # 常驻伤害跳字累加器 (开局 Intro 挂载，持续 -1.0 永久生效)
        "gp_dmg_ft": {
            "id": "gp_dmg_ft",
            "t": "floating_text",
            "tm": "v=_ftd;s=7",
            "tr": ["onIntroStart"],
            "uit": [],
            "pri": 0,
            "trm": 0.0,
            "trs": "",
            "trr": "update",
            "c": 1.0,
            "m": 1.0,
            "d": -1.0,
            "s": "none",
            "ta": "self",
            "mt": "passive",
            "v": "",
            "ms": "",
            "st": 0,
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": [],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },
        # 常驻治疗跳字累加器
        "gp_heal_ft": {
            "id": "gp_heal_ft",
            "t": "floating_text",
            "tm": "v=_fth;s=6",
            "tr": ["onIntroStart"],
            "uit": [],
            "pri": 0,
            "trm": 0.0,
            "trs": "",
            "trr": "update",
            "c": 1.0,
            "m": 1.0,
            "d": -1.0,
            "s": "none",
            "ta": "self",
            "mt": "passive",
            "v": "",
            "ms": "",
            "st": 0,
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": [],
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },

        # -------------------------------------------------------------------
        # [阿尔茜 Arcee 官方技能组]
        # 基准属性（R5 L50）：攻击力 3485，暴击率 32%，暴击伤害 1.70x
        # -------------------------------------------------------------------
        # 1. 爆头射击 (Headshot Direct) - 远程暴击额外直接扣血 60% 攻击力 (2091点)
        #    触发条件：暴击 (onCrit) 且为远程攻击或S1子弹 (level=Ranged,Special1)
        #    基础几率：50% (c: 0.5)
        "arcee_headshot_direct": {
            "id": "arcee_headshot_direct",
            "t": "dmg_direct",
            "tm": "",
            "tr": ["onCrit"],
            "uit": ["onCrit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "level=Ranged,Special1",
            "trr": "repeat",
            "c": 0.5,                    # 基础 50% 触发几率
            "m": 2091.0,                 # 60% 攻击力 (3485 * 0.6 = 2091 点直接伤害)
            "d": 0.5,                    # 单 Tick 结算即时扣除
            "s": "none",
            "ta": "opponent",            # 作用于对手
            "mt": "passive",             # passive，不生成血条下重复图标
            "v": "",
            "ms": "",
            "st": 0,
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": [],                     # 空外观列表：直接伤害由跳字展现，不生成独立血条挂件
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },

        # 2. 爆头流血 (Headshot Bleed DOT) - 远程暴击施加 3 秒流血 DOT (非冲锋状态)
        #    触发条件：暴击 (onCrit) 且为远程/S1，且敌人未前冲 (opponent:state!=Dash,Run)
        #    呼出文字：BLEED ("appr_arcee_bleed")
        #    总伤害：60% 攻击力 (2091点)，3秒内每0.5秒一跳 (每跳 348点)
        #    基础几率：50% (c: 0.5)
        #    最大堆叠数：st: 10 (允许多层独立流血同时存在并显示数字角标)
        "arcee_headshot_dot": {
            "id": "arcee_headshot_dot",
            "t": "dmg_bleed",
            "tm": "",
            "tr": ["onCrit"],
            "uit": ["onCrit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "level=Ranged,Special1;opponent:state!=Dash,Run",
            "trr": "repeat",
            "c": 0.5,                    # 基础 50% 几率
            "m": 2091.0,                 # 3秒总伤害 2091 点 (每跳 348 伤害)
            "d": 3.0,                    # 持续 3 秒
            "s": "none",
            "ta": "opponent",
            "mt": "debuff",              # 敌方血条下方生成倒计时圆环图标
            "v": "",
            "ms": "",
            "st": 10,                    # StackLimit=10，支持多层堆叠而不是替换倒计时！
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": ["appr_arcee_bleed"],   # 关联能量块滴液流血图标与呼出大字 "BLEED"
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },

        # 3. 爆头冲锋惩罚 (Headshot Rush) - 敌人冲刺 (Dash/Run) 中枪暴击时 100% 必出流血
        #    触发条件：暴击 (onCrit) 且为远程/S1，且敌人正在冲刺 (opponent:state=Dash,Run)
        #    呼出文字：HEADSHOT ("appr_arcee_headshot")
        #    几率：100% (c: 1.0)
        #    堆叠策略：同属 dmg_bleed，与普通流血和S2流血共享同一血条图标并累加角标数字
        "arcee_headshot_rush": {
            "id": "arcee_headshot_rush",
            "t": "dmg_bleed",
            "tm": "",
            "tr": ["onCrit"],
            "uit": ["onCrit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "level=Ranged,Special1;opponent:state=Dash,Run", # 敌人冲锋状态判定
            "trr": "repeat",
            "c": 1.0,                    # 前冲中枪暴击 100% 必出流血！
            "m": 2091.0,
            "d": 3.0,
            "s": "none",
            "ta": "opponent",
            "mt": "debuff",
            "v": "",
            "ms": "",
            "st": 10,                    # StackLimit=10
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": ["appr_arcee_headshot"],# 独占呼出大字 "HEADSHOT"
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },

        # 4. S2 暴击流血 (Special Attack 2 Bleed)
        #    触发条件：S2 暴击 (onCrit, level=Special2)
        #    呼出文字：BLEED ("appr_arcee_bleed")
        #    几率：100% (c: 1.0)
        #    总伤害：108% 攻击力 (3485 * 1.08 = 3764 点)，持续 4 秒 (每跳 470 点)
        #    堆叠策略：同样归入 dmg_bleed，血条图标与普通流血自动合并堆叠，多层角标累加
        "arcee_s2_bleed": {
            "id": "arcee_s2_bleed",
            "t": "dmg_bleed",            # 统一使用 dmg_bleed，合并至同一 HUD 图标堆叠
            "tm": "",
            "tr": ["onCrit"],
            "uit": ["onCrit"],
            "pri": 0,
            "trm": 0.0,
            "trs": "level=Special2",
            "trr": "repeat",
            "c": 1.0,                    # 100% 触发几率
            "m": 3764.0,                 # 108% 攻击力 (4秒总伤害 3764 点，每跳 470 伤害)
            "d": 4.0,                    # 持续 4 秒
            "s": "none",
            "ta": "opponent",
            "mt": "debuff",
            "v": "",
            "ms": "",
            "st": 10,                    # StackLimit=10
            "g": "",
            "gc": 0.0,
            "gcv": "",
            "rcv": "",
            "ti": 0,
            "a": ["appr_arcee_bleed"],   # 关联呼出大字 "BLEED"
            "au": [],
            "rh": 0.0,
            "ra": 0.0,
        },
    }

    # 为全员 78 位英雄注册 SP1 / SP2 / SP3 技能名呼出修饰器
    # 挂载在 onSpecial1Activate / onSpecial2Activate / onSpecial3Activate 触发点
    for bid in BOT_SP_MAP:
        for lvl in (1, 2, 3):
            mod_id = f"sp_callout_{bid}_{lvl}"
            res[mod_id] = {
                "id": mod_id,
                "t": "sp_callout",
                "tm": "",
                "tr": [f"onSpecial{lvl}Activate"],
                "uit": [f"onSpecial{lvl}Activate"],
                "pri": 0,
                "trm": 0.0,
                "trs": "",
                "trr": "repeat",
                "c": 1.0,
                "m": 0.0,
                "d": 1.0,
                "s": "none",
                "ta": "self",
                "mt": "buff",
                "v": "",
                "ms": "",
                "st": 0,
                "g": "",
                "gc": 0.0,
                "gcv": "",
                "rcv": "",
                "ti": 0,
                "a": [f"appr_sp_{bid}_{lvl}"],
                "au": [],
                "rh": 0.0,
                "ra": 0.0,
            }

    return res


# ---------------------------------------------------------------------------
# 5. 角色与技能绑定表 (bot_abilities)
# ---------------------------------------------------------------------------
BOT_ABILITIES_MAP = {
    # 阿尔茜：配置爆头直接扣血、爆头3秒流血、冲锋100%流血强化、以及S2暴击流血
    "arcee_gs_deluxe2014": [
        "arcee_headshot_direct",
        "arcee_headshot_dot",
        "arcee_headshot_rush",
        "arcee_s2_bleed",
    ],
}


def bot_abilities(bot_id):
    """查询指定金刚拥有的全部能力修饰器 ID 列表（包含通用 SP 技名呼出与专属技能）。"""
    sp_mods = [f"sp_callout_{bot_id}_{lvl}" for lvl in (1, 2, 3)] if bot_id in BOT_SP_MAP else []
    return sp_mods + BOT_ABILITIES_MAP.get(bot_id, [])
