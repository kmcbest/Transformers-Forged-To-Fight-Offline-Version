import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import json
import os
from pathlib import Path
from collections import defaultdict

# 1. Connect to DB and fetch all characters
conn = sqlite3.connect("Server/tftf_database.db")
cur = conn.cursor()
cur.execute("SELECT bot_id, name_zh, name_en, class, faction FROM characters ORDER BY name_zh")
characters = {}
for r in cur.fetchall():
    characters[r[0]] = {
        "id": r[0],
        "name_zh": r[1] or r[0],
        "name_en": r[2] or r[0],
        "class": r[3] or "",
        "faction": r[4] or ""
    }

# Also fetch character abilities from DB
cur.execute("SELECT bot_id, category, title_zh, title_en, desc_zh, pua_icon FROM character_abilities")
db_rows = cur.fetchall()
conn.close()

bot_texts = defaultdict(list)
for bot_id, cat, t_zh, t_en, d_zh, icon in db_rows:
    t = f"{t_zh or ''} {t_en or ''} {d_zh or ''} {icon or ''}"
    bot_texts[bot_id].append(t.lower())

# Also scan Server/character_data/*.json for ability text keywords
char_dir = Path("Server/character_data")
for p in char_dir.glob("*.json"):
    # Skip alias or raw pulled files
    if p.stem == "elita_one_gs_kabam" or p.stem.endswith("_pulled"):
        continue
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        bid = d.get("bot_id", p.stem)
        if bid in characters:
            bot_texts[bid].append(json.dumps(d, ensure_ascii=False).lower())
    except Exception:
        pass

# Also scan Server/abilities/bots/*.py
py_dir = Path("Server/abilities/bots")
for p in py_dir.glob("*.py"):
    text = p.read_text(encoding="utf-8", errors="ignore").lower()
    stem = p.stem
    for bid in characters:
        if stem in bid:
            bot_texts[bid].append(text)

print(f"Total characters mapped: {len(characters)}")

# Define canonical basic abilities list with official/cleaned descriptions
CANONICAL_ABILITIES = [
    # --- 持续伤害 (Damage Over Time) ---
    {
        "id": "bleed",
        "name_zh": "流血",
        "name_en": "Bleed",
        "category": "持续伤害",
        "pua_icon": "E401",
        "desc_zh": "流失的能量晶体会持续造成直接伤害。",
        "desc_en": "Bleeding energon causes direct damage over time.",
        "keywords": ["流血", "bleed", "出血", "能量晶体流失", "e401"]
    },
    {
        "id": "burn",
        "name_zh": "燃烧",
        "name_en": "Burn",
        "category": "持续伤害",
        "pua_icon": "E41D",
        "desc_zh": "持续造成能量伤害。",
        "desc_en": "Deals energy damage over time.",
        "keywords": ["燃烧", "burn", "烧伤", "地狱弹药", "e41d", "e403"]
    },
    {
        "id": "shock",
        "name_zh": "震击",
        "name_en": "Shock",
        "category": "持续伤害",
        "pua_icon": "E914",
        "desc_zh": "持续造成电磁能量伤害。",
        "desc_en": "Deals electrical energy damage over time.",
        "keywords": ["震击", "shock", "震惊", "漏电", "e914"]
    },
    {
        "id": "acid",
        "name_zh": "酸液",
        "name_en": "Acid",
        "category": "持续伤害",
        "pua_icon": "E524",
        "desc_zh": "持续造成酸性伤害。",
        "desc_en": "Deals corrosive acid damage over time.",
        "keywords": ["酸液", "acid", "强酸", "腐蚀", "e524"]
    },
    {
        "id": "dark_burn",
        "name_zh": "黑暗燃烧",
        "name_en": "Dark Burn",
        "category": "持续伤害",
        "pua_icon": "E810",
        "desc_zh": "造成瞬时黑暗能量伤害。",
        "desc_en": "Deals instant dark energy damage.",
        "keywords": ["暗烧伤", "dark burn", "黑暗燃烧", "混沌燃烧", "e810"]
    },
    {
        "id": "headshot",
        "name_zh": "爆头射击",
        "name_en": "Headshot",
        "category": "持续伤害",
        "pua_icon": "E401",
        "desc_zh": "爆头导致瞬间的能量晶体流失伤害并持续造成直接伤害，对手回避时额外承受伤害。",
        "desc_en": "Headshots cause instant damage and bleeding damage over time, dealing extra damage if the opponent evades.",
        "explicit_bots": ["arcee_gs_deluxe2014"],
        "keywords": ["爆头", "headshot", "head shot"]
    },

    # --- 防御与削弱 (Armor & Defense) ---
    {
        "id": "armor_break",
        "name_zh": "破甲",
        "name_en": "Armor Break",
        "category": "防御削弱",
        "pua_icon": "E516",
        "desc_zh": "移除护甲增益，降低护甲评级并提升受到攻击的伤害量。",
        "desc_en": "Removes armor buffs and reduces armor rating, amplifying incoming damage.",
        "keywords": ["破甲", "armor break", "装甲击碎", "撕裂装甲", "e516"]
    },
    {
        "id": "armor_pen",
        "name_zh": "护甲穿透",
        "name_en": "Armor Penetration",
        "category": "攻击特长",
        "pua_icon": "E409",
        "desc_zh": "忽略对手当前护甲值的固定百分比造成伤害。",
        "desc_en": "Ignores a percentage of the opponent's current armor.",
        "keywords": ["护甲穿透", "穿甲", "armor pen", "armor pierce"]
    },
    {
        "id": "armor_buff",
        "name_zh": "护甲增益",
        "name_en": "Armor Buff",
        "category": "属性增益",
        "pua_icon": "E517",
        "desc_zh": "临时提升装甲厚度，降低受到攻击的伤害。",
        "desc_en": "Temporarily increases armor thickness, reducing damage from incoming attacks.",
        "keywords": ["护甲增益", "装甲增益", "armor buff", "获得护甲", "e517", "e501"]
    },
    {
        "id": "permanent_armor",
        "name_zh": "永久护甲",
        "name_en": "Permanent Armor",
        "category": "属性增益",
        "pua_icon": "E501",
        "desc_zh": "全程持续获得固定的伤害减免，不可被破甲效果移除。",
        "desc_en": "Provides permanent passive damage reduction that cannot be removed by Armor Break.",
        "explicit_bots": [
            "fte_optimus_gs_t3",
            "optimusprime_sg_voyager2015",
            "optimusprimal_bw_mp32",
            "megatron_cin_rotf",
            "grindor_cin_rotf",
            "tantrum_gs_kabam"
        ],
        "keywords": ["永久护甲", "permanent armor", "天然护甲"]
    },
    {
        "id": "shield",
        "name_zh": "护盾",
        "name_en": "Shield",
        "category": "生存防御",
        "pua_icon": "E515",
        "desc_zh": "展开力场吸收来袭伤害，优先于生命值消耗。",
        "desc_en": "Deploys a forcefield that absorbs incoming damage before reducing health.",
        "keywords": ["护盾", "shield", "屏蔽", "力场", "e515"]
    },
    {
        "id": "shield_breaker",
        "name_zh": "破盾",
        "name_en": "Shield Break",
        "category": "机制克制",
        "pua_icon": "E807",
        "desc_zh": "粉碎对手的护盾力场。",
        "desc_en": "Shatters the opponent's shield.",
        "keywords": ["破盾", "shield breaker", "粉碎力场", "护盾崩解", "e807", "shdbrk"]
    },

    # --- 行动控制 (Crowd Control) ---
    {
        "id": "stun",
        "name_zh": "眩晕",
        "name_en": "Stun",
        "category": "行动控制",
        "pua_icon": "E605",
        "desc_zh": "临时阻止目标采取任何行动。",
        "desc_en": "Temporarily paralyzes the target, preventing all actions.",
        "keywords": ["眩晕", "stun", "击晕", "e605"]
    },
    {
        "id": "decelerate",
        "name_zh": "减速",
        "name_en": "Decelerate",
        "category": "行动控制",
        "pua_icon": "E952",
        "desc_zh": "阻止对手躲避攻击，并减少对手行动时的能量流速。",
        "desc_en": "Prevents the opponent from dodging and slows their power flow.",
        "keywords": ["减速", "decelerate", "缓慢", "e952"]
    },
    {
        "id": "tactical_lockdown",
        "name_zh": "战术封锁",
        "name_en": "Tactical Lockdown",
        "category": "行动控制",
        "pua_icon": "E419",
        "desc_zh": "封印对手全部特殊攻击，期间对手无法发动任何特殊技。",
        "desc_en": "Locks down all special attacks, preventing the opponent from launching any special move.",
        "explicit_bots": ["elita_one_gs"],
        "keywords": ["战术封锁", "tactical lockdown"]
    },
    {
        "id": "fear",
        "name_zh": "恐惧",
        "name_en": "Fear",
        "category": "状态减益",
        "pua_icon": "E41A",
        "desc_zh": "背对敌人或逃跑时受到威慑抑制，大幅降低攻击与机动力。",
        "desc_en": "Intimidates fleeing opponents, significantly penalizing attack rating and mobility.",
        "keywords": ["恐惧", "fear", "e41a"]
    },
    {
        "id": "daze",
        "name_zh": "目眩",
        "name_en": "Daze",
        "category": "状态减益",
        "pua_icon": "E519",
        "desc_zh": "使对手陷入目眩，大幅降低其远程攻击命中率（基础远程与特殊远程攻击大概率无法命中）。",
        "desc_en": "Dazes the opponent, causing their basic and special ranged attacks to miss.",
        "explicit_bots": ["scorponok_bw_kabam"],
        "keywords": ["目眩", "daze"]
    },

    # --- 机动与格斗状态 (Mobility & Combat State) ---
    {
        "id": "evade",
        "name_zh": "规避",
        "name_en": "Evade",
        "category": "机动防御",
        "pua_icon": "E509",
        "desc_zh": "自动闪避即将到来的攻击。",
        "desc_en": "Automatically evade incoming attack.",
        "keywords": ["规避", "evade", "回避", "闪避", "近战规避", "e509", "e518"]
    },
    {
        "id": "precision",
        "name_zh": "精准",
        "name_en": "Precision",
        "category": "攻击特长",
        "pua_icon": "E409",
        "desc_zh": "增加暴击命中几率。",
        "desc_en": "Increases critical hit chance.",
        "keywords": ["精准", "precision", "精度", "反闪避", "规避克制", "e92a"]
    },
    {
        "id": "unstoppable",
        "name_zh": "不可阻挡",
        "name_en": "Unstoppable",
        "category": "进攻强化",
        "pua_icon": "E915",
        "desc_zh": "进攻动作无视对手攻击冲击与受击打断。",
        "desc_en": "Shrugs off hit reactions; attacks cannot be interrupted.",
        "keywords": ["不可阻挡", "unstoppable", "势不可挡", "霸体", "无视攻击影响", "e915"]
    },
    {
        "id": "unblockable",
        "name_zh": "无法格挡",
        "name_en": "Unblockable",
        "category": "进攻强化",
        "pua_icon": "E41F",
        "desc_zh": "特定攻击无法被防御格挡，强行贯穿防御。",
        "desc_en": "Certain attacks cannot be blocked, directly piercing defenses.",
        "keywords": ["无法格挡", "unblockable", "不可防御", "破防", "e40a"]
    },
    {
        "id": "counterpunch",
        "name_zh": "灵动反击",
        "name_en": "Counterpunch",
        "category": "战术反制",
        "pua_icon": "E50A",
        "desc_zh": "成功闪避近战或前冲后获得反击契机，可打出硬直或眩晕。",
        "desc_en": "Successful dodges grant counter windows to stagger or stun the opponent.",
        "explicit_bots": ["elita_one_gs"],
        "keywords": ["灵动反击", "反击锦囊"]
    },
    {
        "id": "parry_shield",
        "name_zh": "招架护盾",
        "name_en": "Parry Shield",
        "category": "防御反制",
        "pua_icon": "E911",
        "desc_zh": "成功格挡攻击时吸收冲击，并反弹来袭的近战攻击或远程火力。",
        "desc_en": "Absorbs impact upon successful block and reflects melee or ranged strikes.",
        "keywords": ["招架护盾", "parry", "近战反射", "声波护盾", "e911"]
    },

    # --- 属性与伤害增益/减益 (Buffs & Debuffs) ---
    {
        "id": "attack_buff",
        "name_zh": "攻击增益",
        "name_en": "Attack Buff",
        "category": "属性增益",
        "pua_icon": "E406",
        "desc_zh": "临时增加机体攻击评分与造成的全部伤害。",
        "desc_en": "Temporarily increases overall attack rating and damage dealt.",
        "keywords": ["攻击增益", "attack buff", "狂怒", "提升攻击力", "攻击评级", "e406"]
    },
    {
        "id": "attack_debuff",
        "name_zh": "攻击减益",
        "name_en": "Attack Debuff",
        "category": "状态减益",
        "pua_icon": "E916",
        "desc_zh": "削弱机体动力，临时减少对手攻击评分与输出。",
        "desc_en": "Temporarily reduces the opponent's attack rating and damage output.",
        "keywords": ["攻击减益", "attack debuff", "虚弱", "疲劳", "减少攻击力", "e916"]
    },
    {
        "id": "melee_buff",
        "name_zh": "近战增益",
        "name_en": "Melee Buff",
        "category": "属性增益",
        "pua_icon": "E412",
        "desc_zh": "临时增加近战普通攻击与近战重击的伤害。",
        "desc_en": "Temporarily increases damage dealt by basic and heavy melee attacks.",
        "keywords": ["近战增益", "melee buff", "近战伤害", "e412"]
    },
    {
        "id": "ranged_buff",
        "name_zh": "远程增益",
        "name_en": "Ranged Buff",
        "category": "属性增益",
        "pua_icon": "E413",
        "desc_zh": "临时增加远程攻击的速度、射击频率与伤害。",
        "desc_en": "Temporarily increases ranged attack speed, projectile rate, and damage.",
        "keywords": ["远程增益", "ranged buff", "远程伤害", "远程射击", "e413", "e41b"]
    },
    {
        "id": "special_damage",
        "name_zh": "特殊伤害",
        "name_en": "Special Damage",
        "category": "属性增益",
        "pua_icon": "E419",
        "desc_zh": "增加组合连击与全部特殊攻击造成的破坏力。",
        "desc_en": "Increases damage dealt by combo finishers and special attacks.",
        "keywords": ["特殊伤害", "special damage", "特殊攻击伤害", "特殊技伤害", "e419"]
    },
    {
        "id": "crit_rate_buff",
        "name_zh": "暴击率增益",
        "name_en": "Crit Rate Buff",
        "category": "属性增益",
        "pua_icon": "E40D",
        "desc_zh": "临时增加攻击命中时触发暴击的几率。",
        "desc_en": "Temporarily increases the chance of scoring critical hits.",
        "keywords": ["暴击几率", "暴击率增益", "crit rate", "临界率", "e40d"]
    },
    {
        "id": "crit_rate_debuff",
        "name_zh": "暴击率减益",
        "name_en": "Crit Rate Debuff",
        "category": "状态减益",
        "pua_icon": "E912",
        "desc_zh": "降低对手攻击命中时触发暴击的几率。",
        "desc_en": "Reduces the opponent's chance of scoring critical hits.",
        "keywords": ["暴击率减益", "crit down", "降低暴击", "e912"]
    },
    {
        "id": "crit_damage_buff",
        "name_zh": "暴击伤害增益",
        "name_en": "Crit Damage Buff",
        "category": "属性增益",
        "pua_icon": "E906",
        "desc_zh": "临时增加暴击命中时造成的伤害倍率。",
        "desc_en": "Temporarily increases the damage multiplier of critical hits.",
        "keywords": ["暴击伤害", "严重伤害", "crit damage", "e906"]
    },
    {
        "id": "crit_damage_debuff",
        "name_zh": "暴击伤害减益",
        "name_en": "Crit Damage Debuff",
        "category": "状态减益",
        "pua_icon": "E905",
        "desc_zh": "短时间降低对手产生暴击时造成的伤害深度。",
        "desc_en": "Temporarily reduces the severity of incoming critical hit damage.",
        "keywords": ["暴击伤害减益", "crit dmg down", "e905"]
    },
    {
        "id": "resistance_buff",
        "name_zh": "抗性提升",
        "name_en": "Resistance Buff",
        "category": "生存防御",
        "pua_icon": "E60A",
        "desc_zh": "临时降低即将到来的物理或能量伤害。",
        "desc_en": "Temporarily reduces incoming physical or energy damage.",
        "keywords": ["抗性提升", "resistance buff", "物理抗性", "能量抗性", "e60a"]
    },
    {
        "id": "resistance_debuff",
        "name_zh": "抗性减益",
        "name_en": "Resistance Debuff",
        "category": "防御削弱",
        "pua_icon": "E60A",
        "desc_zh": "降低目标抗性评级，放大其承受的所有伤害。",
        "desc_en": "Reduces target resistance rating, amplifying all incoming damage.",
        "keywords": ["抗性减益", "resistance debuff", "电阻下降", "易伤", "e60a"]
    },

    # --- 能量控制 (Energy & Power) ---
    {
        "id": "power_gain",
        "name_zh": "能量获取",
        "name_en": "Power Gain",
        "category": "能量控制",
        "pua_icon": "E608",
        "desc_zh": "持续进行的被动能量积蓄，加速特殊技能量条充盈。",
        "desc_en": "Passively gains power over time to fill special attack bars faster.",
        "keywords": ["能量获取", "power gain", "功率增益", "能量增加", "e608"]
    },
    {
        "id": "power_flow",
        "name_zh": "能量涌动",
        "name_en": "Power Flow",
        "category": "能量控制",
        "pua_icon": "E408",
        "desc_zh": "提高所有攻击与受击时所产生的能量充能功率。",
        "desc_en": "Increases power generation rate from all attacks and hits taken.",
        "keywords": ["能量涌动", "power flow", "能量功率", "能量模式", "e408"]
    },
    {
        "id": "power_leak",
        "name_zh": "能量流失",
        "name_en": "Power Leak",
        "category": "能量控制",
        "pua_icon": "E607",
        "desc_zh": "随时间推移持续扣减对手一定比例的能量槽。",
        "desc_en": "Drains a percentage of the opponent's power gauge over time.",
        "keywords": ["能量流失", "power leak", "力量泄漏", "消耗能量", "e607"]
    },
    {
        "id": "power_burn",
        "name_zh": "能量燃烧",
        "name_en": "Power Burn",
        "category": "能量控制",
        "pua_icon": "E607",
        "desc_zh": "立即消耗对手的能量槽，并按消耗量造成直接能量伤害。",
        "desc_en": "Instantly burns the opponent's power gauge and deals direct damage based on power lost.",
        "keywords": ["能量燃烧", "power burn", "扣除能量", "e607"]
    },
    {
        "id": "power_lock",
        "name_zh": "能量锁定",
        "name_en": "Power Lock",
        "category": "能量控制",
        "pua_icon": "E523",
        "desc_zh": "临时阻止目标从攻击或被动机制中获取任何能量。",
        "desc_en": "Temporarily prevents the target from gaining power from any source.",
        "keywords": ["能量锁定", "power lock", "阻止获得能量", "e523"]
    },
    {
        "id": "power_steal",
        "name_zh": "能量窃取",
        "name_en": "Power Steal",
        "category": "能量控制",
        "pua_icon": "E607",
        "desc_zh": "盗取对手当前储存的能量槽，并将其转移给自己。",
        "desc_en": "Steals stored power from the opponent and transfers it to the user.",
        "keywords": ["能量窃取", "power steal", "盗取能量"]
    },

    # --- 机制克制与生存 (Utility & Sustain) ---
    {
        "id": "nullify",
        "name_zh": "驱散",
        "name_en": "Nullify",
        "category": "机制克制",
        "pua_icon": "E950",
        "desc_zh": "消除对手身上的增益效果，使其增益立即失效。",
        "desc_en": "Clears active buffs from the opponent, instantly ending their effects.",
        "keywords": ["驱散", "nullify", "无效化", "清除增益", "消除增益", "e950"]
    },
    {
        "id": "purify",
        "name_zh": "净化",
        "name_en": "Purify",
        "category": "机制克制",
        "pua_icon": "E903",
        "desc_zh": "清除自身所承受的伤害减益与负面状态。",
        "desc_en": "Cleanses damaging debuffs and negative status effects from oneself.",
        "keywords": ["净化", "purify", "cleanse", "清除减益", "e903"]
    },
    {
        "id": "repair",
        "name_zh": "修复",
        "name_en": "Repair",
        "category": "生命恢复",
        "pua_icon": "E503",
        "desc_zh": "随时间推移持续修复生命值，或按受损比例回血。",
        "desc_en": "Repairs health over time or restores a percentage of lost health.",
        "keywords": ["修复", "repair", "回血", "自我诊断", "生命回复", "再生", "e503"]
    },
    {
        "id": "heal_block",
        "name_zh": "修复阻止",
        "name_en": "Heal Block",
        "category": "机制克制",
        "pua_icon": "E90C",
        "desc_zh": "临时阻止目标回复生命值，全面抑制回血与再生效果。",
        "desc_en": "Temporarily prevents the target from regaining health, shutting down all healing.",
        "keywords": ["修复阻止", "heal block", "修复格挡", "阻止修复", "禁用回血", "e90c", "e41f"]
    },
    {
        "id": "backfire",
        "name_zh": "逆火",
        "name_en": "Backfire",
        "category": "状态减益",
        "pua_icon": "E901",
        "desc_zh": "对手激活特殊攻击时发生回火反冲，造成直接伤害并打断动作。",
        "desc_en": "Causes backfire recoil when the opponent activates a special attack, dealing damage.",
        "keywords": ["逆火", "backfire", "e901"]
    },
    {
        "id": "willpower",
        "name_zh": "意志力",
        "name_en": "Willpower",
        "category": "生存反制",
        "pua_icon": "E40E",
        "desc_zh": "处于减益状态时，将受到的部分伤害转化为生命值回复。",
        "desc_en": "Converts a portion of incoming damage into health recovery while suffering debuffs.",
        "keywords": ["意志力", "willpower", "减益控制", "e40e"]
    },
    {
        "id": "momentum",
        "name_zh": "冲力充能",
        "name_en": "Momentum",
        "category": "进攻强化",
        "pua_icon": "E910",
        "desc_zh": "通过冲锋、重击或连击积累动能充能，强化后续打击威力。",
        "desc_en": "Builds kinetic charges through dashes and heavy hits to empower subsequent strikes.",
        "keywords": ["冲力", "momentum", "冲压", "冲刺", "e910"]
    },
    {
        "id": "emi_jamming",
        "name_zh": "干扰",
        "name_en": "EMI Jamming",
        "category": "状态减益",
        "pua_icon": "E904",
        "desc_zh": "发射电磁干扰波，降低敌方远程伤害、投射速度与雷达瞄准。",
        "desc_en": "Emits electromagnetic pulses to diminish ranged damage, projectile velocity, and tracking.",
        "keywords": ["干扰", "emi", "jamming", "e904"]
    },
    {
        "id": "dark_energy",
        "name_zh": "暗能量",
        "name_en": "Dark Energy",
        "category": "特殊机制",
        "pua_icon": "E90A",
        "desc_zh": "聚集黑暗能量充能，提高攻击评级并为黑暗场提供动力。",
        "desc_en": "Harvests dark energy charges, boosting attack rating and powering dark fields.",
        "keywords": ["暗能量", "dark energy", "黑暗能量", "e90a"]
    },
    {
        "id": "double_edge",
        "name_zh": "双刃剑",
        "name_en": "Double Edge",
        "category": "高风险增益",
        "pua_icon": "E402",
        "desc_zh": "大幅提升自身攻击力，但持续承受直接流血反噬伤害。",
        "desc_en": "Massively boosts attack power at the cost of continuous self-inflicted bleed recoil.",
        "keywords": ["双刃剑", "double edge", "e402"]
    },
    {
        "id": "system_upgrade",
        "name_zh": "机体升级",
        "name_en": "System Upgrade",
        "category": "特殊机制",
        "pua_icon": "E306",
        "desc_zh": "构建进攻、防御或能量系统模块升级，全面强化机体性能。",
        "desc_en": "Constructs offensive, defensive, or energy module upgrades to enhance chassis performance.",
        "keywords": ["升级", "upgrade", "系统构建", "e306"]
    },
    {
        "id": "venom_charge",
        "name_zh": "毒液充能",
        "name_en": "Venom Charge",
        "category": "特殊机制",
        "pua_icon": "E524",
        "desc_zh": "积累毒囊充能，转化为致命神经毒素与腐蚀伤害。",
        "desc_en": "Accumulates venom charges, converting them into neurotoxins and corrosive damage.",
        "keywords": ["毒液", "venom", "毒囊"]
    }
]

# Map characters to each ability based on keyword detection or explicit bots
final_catalog = []
for item in CANONICAL_ABILITIES:
    if "explicit_bots" in item:
        matched_bots = [
            {
                "bot_id": bid,
                "name_zh": characters[bid]["name_zh"],
                "name_en": characters[bid]["name_en"],
                "faction": characters[bid]["faction"],
                "class": characters[bid]["class"]
            }
            for bid in item["explicit_bots"]
            if bid in characters
        ]
    else:
        kws = item["keywords"]
        matched_bots = []
        for bid, cinfo in characters.items():
            all_t = " ".join(bot_texts[bid])
            if any(kw.lower() in all_t for kw in kws):
                matched_bots.append({
                    "bot_id": bid,
                    "name_zh": cinfo["name_zh"],
                    "name_en": cinfo["name_en"],
                    "faction": cinfo["faction"],
                    "class": cinfo["class"]
                })
    
    # Sort matched bots by name_zh
    matched_bots.sort(key=lambda x: x["name_zh"])
    
    # Convert hex to unicode representation
    pua_hex = item["pua_icon"]
    pua_char = ""
    if pua_hex:
        try:
            pua_char = chr(int(pua_hex, 16))
        except Exception:
            pua_char = ""

    final_catalog.append({
        "id": item["id"],
        "name_zh": item["name_zh"],
        "name_en": item["name_en"],
        "category": item["category"],
        "pua_icon": pua_hex,
        "pua_char": pua_char,
        "desc_zh": item["desc_zh"],
        "desc_en": item["desc_en"],
        "bot_count": len(matched_bots),
        "associated_bots": matched_bots
    })

print(f"\nGenerated {len(final_catalog)} canonical basic abilities.")
for item in final_catalog[:10]:
    print(f"  [{item['pua_icon']}] {item['name_zh']} ({item['name_en']}) - {item['bot_count']} bots: {item['desc_zh']}")

# Save to tools/basic_abilities.json
out_json_path = Path("tools/basic_abilities.json")
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump({
        "meta": {
            "title": "TFTF Common Basic Abilities Catalog",
            "version": "1.4",
            "total_abilities": len(final_catalog),
            "total_characters": len(characters),
            "updated_at": "2026-11-02"
        },
        "characters_all": list(characters.values()),
        "abilities": final_catalog
    }, f, ensure_ascii=False, indent=2)

print(f"Saved {out_json_path} successfully!")
