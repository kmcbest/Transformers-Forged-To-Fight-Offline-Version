#!/usr/bin/env python3
"""
Bot Ability Implementation: 闪电 (Blitzwing)
===========================================
Bot ID: blitzwing_gs
阵营: 霸天虎 (Decepticon) | 职业: 战术系 (Tactician)

【三变形态切换与重击变形战斗机制】：
-----------------------------------------------------------------------------
1. [开局被动 - 坦克形态 / Tank Mode]
   - 开局默认进入坦克形态，HUD 显示白色坦克图标 (\\uE902)。
   - 处于坦克形态时，重击变形为坦克炮击 (move_heavy_megatron_gs_shoot)。
2. [长按防御变形 - 战机形态 / Jet Mode]
   - 在战斗中按住防御 1.0 秒，触发三变变形切换至战机形态。
   - 图标切换为白色战机图标 (\\uE184)。
   - 处于战机形态时，重击变形为战机低空冲撞 (move_heavy_ramjet_donut)。
   - 再次按住防御 1.0 秒可无缝切换回坦克形态。
-----------------------------------------------------------------------------
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from ..core import (
    AbilityColor,
    make_statmod_appearance,
    validate_statmod,
)
from ..registry import register_bot

BOT_ID = "blitzwing_gs"


@register_bot(BOT_ID, name_zh="闪电", desc="霸天虎战术系三变战士，长按防御1秒切换坦克形态(重击放炮)与战机形态(重击冲撞)")
def build_blitzwing_abilities(base_hp: float = 38250.0, base_atk: float = 2795.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 坦克形态 (Tank Mode): 白色 E902 图标，开局常驻
    appr_tank = make_statmod_appearance(
        appr_id="appr_blitzwing_tank_mode",
        callout_text="坦克形态",
        desc="闪电处于坦克形态，重击变形为坦克炮击",
        short_desc="坦克形态",
        pua_icon="\uE902",
        color=AbilityColor.WHITE_SPECIAL,
        show_callout=True,
        active_desc="坦克形态",
    )
    mod_tank = {
        "id": "blitzwing_tank_mode",
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
        "st": 1,
        "g": "blitzwing_stance",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blitzwing_tank_mode"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_tank)
    mods["blitzwing_tank_mode"] = mod_tank
    appears["appr_blitzwing_tank_mode"] = appr_tank

    # 2. 战机形态 (Jet Mode): 白色 E184 图标，持防1秒切换
    appr_jet = make_statmod_appearance(
        appr_id="appr_blitzwing_jet_mode",
        callout_text="战机形态",
        desc="闪电处于战机形态，重击变形为战机冲撞",
        short_desc="战机形态",
        pua_icon="\uE184",
        color=AbilityColor.WHITE_SPECIAL,
        show_callout=True,
        active_desc="战机形态",
    )
    mod_jet = {
        "id": "blitzwing_jet_mode",
        "t": "attack_buff",
        "tm": "",
        "tr": [],
        "uit": [],
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
        "st": 1,
        "g": "blitzwing_stance",
        "gc": 0.0,
        "gcv": "",
        "rcv": "",
        "ti": 0,
        "a": ["appr_blitzwing_jet_mode"],
        "au": [],
        "rh": 0.0,
        "ra": 0.0,
    }
    validate_statmod(mod_jet)
    mods["blitzwing_jet_mode"] = mod_jet
    appears["appr_blitzwing_jet_mode"] = appr_jet

    return mods, appears, buffs
