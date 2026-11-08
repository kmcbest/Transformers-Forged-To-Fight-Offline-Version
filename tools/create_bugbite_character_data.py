import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

# 1. Create Server/character_data/bugbite_gs_kabam.json
bugbite_data = {
    "bot_id": "bugbite_gs_kabam",
    "name_zh": "杀人蜂",
    "name_en": "Bug Bite",
    "faction": "mercenary",
    "class": "braw",
    "signature": {
        "title_zh": "背叛之刺",
        "title_en": "Traitor's Sting",
        "desc_zh": "杀人蜂狡诈地突破敌人的防御。每当进入近战距离，获得能量涌动与近战狂乱增益，近战伤害提升25%。",
        "pua_icon": "E99F",
        "ui_trigger": "none"
    },
    "special_attacks": {
        "sp1": {
            "name_zh": "音波冲击",
            "name_en": "Sonic Blast",
            "effects": [
                {
                    "title_zh": "暴击伤害",
                    "title_en": "Crit Damage",
                    "desc_zh": "技能发动过程中暴击伤害提升60%",
                    "pua_icon": "0xe906"
                }
            ],
            "desc_zh": "技能发动过程中暴击伤害提升60%",
            "pua_icon": "0xe906",
            "ui_trigger": "onSpecial1Hit"
        },
        "sp2": {
            "name_zh": "蜂刺毒弹",
            "name_en": "Wasp Sting",
            "effects": [
                {
                    "title_zh": "能量锁定",
                    "title_en": "Power Lock",
                    "desc_zh": "命中时100%概率触发能量锁定，阻止对方获得能量，持续10秒",
                    "pua_icon": "0xe523"
                }
            ],
            "desc_zh": "命中时100%概率触发能量锁定，阻止对方获得能量，持续10秒",
            "pua_icon": "0xe523",
            "ui_trigger": "onSpecial2Hit"
        },
        "sp3": {
            "name_zh": "碎玻璃毒气终结",
            "name_en": "Glass Gas Crash",
            "effects": [
                {
                    "title_zh": "不可阻挡",
                    "title_en": "Unstoppable",
                    "desc_zh": "技能结束后获得7.5秒的不可阻挡增益。",
                    "pua_icon": "E915"
                }
            ],
            "desc_zh": "技能结束后获得7.5秒的不可阻挡增益与毒气破甲效果。",
            "pua_icon": "E915",
            "ui_trigger": "onSpecial3Hit"
        }
    },
    "synergies": [
        {
            "title_zh": "盟友——威震天、红蜘蛛",
            "title_en": "Allies – Megatron, Starscream",
            "desc_zh": "+10%~20% 暴击伤害。",
            "pua_icon": "",
            "bonus_heroes": []
        },
        {
            "title_zh": "敌人——大黄蜂、飞过山",
            "title_en": "Enemies – Bumblebee, Cliffjumper",
            "desc_zh": "+15% 攻击评级。",
            "pua_icon": "",
            "bonus_heroes": []
        }
    ],
    "basic_abilities": [
        {
            "title_zh": "近战增益",
            "title_en": "Melee Buff",
            "desc_zh": "增加近战攻击伤害。",
            "desc_en": "Increases melee damage dealt.",
            "pua_icon": "E412"
        },
        {
            "title_zh": "不可阻挡",
            "title_en": "Unstoppable",
            "desc_zh": "进攻动作无视对手攻击冲击。",
            "desc_en": "Attacks cannot be interrupted.",
            "pua_icon": "E915"
        }
    ],
    "game_abilities": []
}

bb_json_path = Path("Server/character_data/bugbite_gs_kabam.json")
bb_json_path.write_text(json.dumps(bugbite_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[+] Wrote {bb_json_path}")

# 2. Update soundblaster, thrust, ramjet, dirge in Server/character_data/
for bot_name in ["soundblaster_gs_mp13b", "thrust_gs_deluxe2008", "ramjet_gs_deluxe2008", "dirge_gs_deluxe2008"]:
    p = Path(f"Server/character_data/{bot_name}.json")
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        d["faction"] = "mercenary"
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[+] Updated faction to mercenary in {p}")

# 3. Update Server/bot_names_zh.json
bn_path = Path("Server/bot_names_zh.json")
bn_data = json.loads(bn_path.read_text(encoding="utf-8"))
bn_data["bugbite_gs_kabam"] = {
    "en": "Bug Bite",
    "zh": "杀人蜂",
    "faction": "雇佣兵",
    "note": "雇佣兵 格斗系"
}
for bot_name in ["soundblaster_gs_mp13b", "thrust_gs_deluxe2008", "ramjet_gs_deluxe2008", "dirge_gs_deluxe2008"]:
    if bot_name in bn_data:
        bn_data[bot_name]["faction"] = "雇佣兵"

bn_path.write_text(json.dumps(bn_data, ensure_ascii=False, indent=4), encoding="utf-8")
print(f"[+] Updated {bn_path}")

# 4. Update Server/sp3_timings.json
sp3_path = Path("Server/sp3_timings.json")
sp3_data = json.loads(sp3_path.read_text(encoding="utf-8"))
sp3_data["bugbite_gs_kabam"] = {
    "intervals": [[4033, 5866]],
    "props": {"leftgun": [[0, 0]], "gasgun": [[0, 0]]},
    "notes": "杀人蜂 (Bug Bite) - 借用飞过山S3舞台"
}
sp3_path.write_text(json.dumps(sp3_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[+] Updated {sp3_path}")
