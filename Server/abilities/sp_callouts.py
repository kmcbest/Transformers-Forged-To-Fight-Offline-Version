#!/usr/bin/env python3
"""
TFTF Universal SP Callout System
================================
负责为全员 78 位变形金刚生成必杀技释放时 1 秒的技能名称 Callout Text。
"""

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


def build_sp_callout_appears():
    """定义修饰器的视觉效果、Unicode PUA 图标字形、呼出文字及纯 6 位 Hex 颜色。"""
    res = {}
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


def build_sp_callout_statmods():
    """为全员 78 位英雄生成 SP1 / SP2 / SP3 技能名呼出修饰器。"""
    res = {}
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
