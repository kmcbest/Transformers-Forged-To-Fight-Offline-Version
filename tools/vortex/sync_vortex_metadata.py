import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# 1. Sync portraits (Strictly within ROOT repository)
redeco_dir = ROOT / "assets_redeco"
redeco_dir.mkdir(parents=True, exist_ok=True)

portraits_dir = ROOT / "extracted_apk" / "assets" / "assetpack" / "portraits_odr" / "portraits"
quest_dir = ROOT / "extracted_apk" / "assets" / "assetpack" / "questboard_odr" / "questboard"

p_large = portraits_dir / "portrait_grind_c_rotf_large.png"
p_small = portraits_dir / "portrait_grind_c_rotf_small.jpg"
p_quest = quest_dir / "portrait_grind_c_rotf_quest.png"

for src, dst_name in [
    (p_large, "portrait_vortex_gs_large.png"),
    (p_large, "portrait_vortex_large.png"),
    (p_large, "vortex_gs.png"),
    (p_large, "vortex.png"),
    (p_small, "portrait_vortex_gs_small.jpg"),
    (p_small, "portrait_vortex_small.jpg"),
    (p_quest, "portrait_vortex_gs_quest.png"),
    (p_quest, "portrait_vortex_quest.png"),
]:
    dst = redeco_dir / dst_name
    if src.exists():
        shutil.copy2(src, dst)
        print(f"[✓] Copied portrait: {dst_name}")

# 2. Sync bot_names_zh.json (Strictly within ROOT repository)
vortex_zh = {
    "en": "Vortex",
    "zh": "旋风",
    "faction": "霸天虎",
    "note": "塞伯坦陨落·爆破系",
    "desc": "战车队阴险狂暴的突击兵与空中支援专家。旋风性格残忍好斗，狂热嗜杀，装备高频旋转离子切刃与重型导弹发射器，能够在半空化作杀戮旋风将一切敌人绞为碎片。"
}

for zh_path in [
    ROOT / "bot_names_zh.json",
    ROOT / "Server" / "bot_names_zh.json",
]:
    if zh_path.exists():
        data = json.loads(zh_path.read_text(encoding="utf-8"))
        data["vortex_gs"] = vortex_zh
        zh_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        print(f"[✓] Updated {zh_path}")

# 3. Sync custom_special_attacks.json & regenerate special_attacks_zh.h
sp_path = ROOT / "assets" / "xlate" / "custom_special_attacks.json"
sp_data = json.loads(sp_path.read_text(encoding="utf-8"))
vortex_sp_entry = {
    "display_name": "旋风",
    "specials": [
        {
            "name": "离子切刃突袭",
            "desc": "旋风疾速突进挥舞双臂高能离子刃，给予敌人致命的高频离子切割。"
        },
        {
            "name": "狂暴旋翼切割",
            "desc": "旋翼急速翻转横扫，以狂风般的烈度撕裂阻挡前方的强敌。"
        },
        {
            "name": "塞伯坦空中死神",
            "desc": "变形为武装直升机呼啸升空，倾泻制导空对地导弹实施毁灭性饱和轰炸。"
        }
    ]
}
sp_data.setdefault("bots", {})["vortex"] = vortex_sp_entry
sp_data["bots"]["vortex_gs"] = vortex_sp_entry
sp_path.write_text(json.dumps(sp_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[✓] Updated {sp_path}")

subprocess.run([sys.executable, str(ROOT / "tools" / "generate_special_attacks.py")], check=True)
print("[✓] Regenerated tools/nativehook/special_attacks_zh.h")

# 4. Update tools/nativehook/hook.c
hook_path = ROOT / "tools" / "nativehook" / "hook.c"
hook_text = hook_path.read_text(encoding="utf-8")
nl = "\r\n" if "\r\n" in hook_text else "\n"

if '"vortex_gs"' not in hook_text:
    target_art = '    { "onslaught_gs", "onslaught_gs" },'
    repl_art = f'    {{ "onslaught_gs", "onslaught_gs" }},{nl}    {{ "vortex_gs", "vortex_gs" }},'
    assert target_art in hook_text, "Could not find onslaught_gs in ART_BASE_MAP"
    hook_text = hook_text.replace(target_art, repl_art, 1)
    print("[✓] Added vortex_gs to ART_BASE_MAP")

if 'strstr(k, "VORTEX")' not in hook_text:
    target_ons = (
        f'        if (strstr(k, "ONSLAUGHT") || strstr(k, "onslaught") || strstr(k, "Onslaught")) {{{nl}'
        f'            if (strstr(k, "BIO") || strstr(k, "desc") || strstr(k, "DESC") || strstr(k, "Bio")) {{{nl}'
        f'                return g_strnew("战车队冷酷沉着的战术指挥官，重装炮火专家。他擅长制定周密残忍的突袭计划，身披重甲，背负双联防空火箭炮与小臂转轮重机炮，在战场上以压倒性的火力粉碎一切阻碍。");{nl}'
        f'            }}{nl}'
        f'            return g_strnew("袭击");{nl}'
        f'        }}'
    )
    vortex_block = (
        f'{nl}        if (strstr(k, "VORTEX") || strstr(k, "vortex") || strstr(k, "Vortex")) {{{nl}'
        f'            if (strstr(k, "BIO") || strstr(k, "desc") || strstr(k, "DESC") || strstr(k, "Bio")) {{{nl}'
        f'                return g_strnew("战车队阴险狂暴的突击兵与空中支援专家。旋风性格残忍好斗，狂热嗜杀，装备高频旋转离子切刃与重型导弹发射器，能够在半空化作杀戮旋风将一切敌人绞为碎片。");{nl}'
        f'            }}{nl}'
        f'            return g_strnew("旋风");{nl}'
        f'        }}'
    )
    assert target_ons in hook_text, "Could not find ONSLAUGHT block in hook_162"
    hook_text = hook_text.replace(target_ons, target_ons + vortex_block, 1)
    print("[✓] Added vortex localization to hook_162")

hook_path.write_text(hook_text, encoding="utf-8")

# 5. Update Server/gamedata.py (Strictly within ROOT repository)
gd_path = ROOT / "Server" / "gamedata.py"
if gd_path.exists():
    gd_text = gd_path.read_text(encoding="utf-8")
    nl_gd = "\r\n" if "\r\n" in gd_text else "\n"
    
    if '"vortex_gs"' not in gd_text:
        # BASE_HEROES
        anchor_hero = '    "grindor_cin_rotf":             ("decepticon", "braw", 5),'
        repl_hero = f'    "grindor_cin_rotf":             ("decepticon", "braw", 5),{nl_gd}    "vortex_gs":                    ("decepticon", "braw", 5),'
        assert anchor_hero in gd_text, f"Could not find grindor_cin_rotf in BASE_HEROES in {gd_path}"
        gd_text = gd_text.replace(anchor_hero, repl_hero, 1)

        # _ART_BASE
        anchor_art = '    "grindor_cin_rotf": "grind_c_rotf",'
        repl_art = f'    "grindor_cin_rotf": "grind_c_rotf",{nl_gd}    "vortex_gs": "vortex_gs",'
        assert anchor_art in gd_text, f"Could not find grindor_cin_rotf in _ART_BASE in {gd_path}"
        gd_text = gd_text.replace(anchor_art, repl_art, 1)

        # _BOT_NAMES
        anchor_bot = '    "grindor_cin_rotf": "Grindor",'
        repl_bot = f'    "grindor_cin_rotf": "Grindor",{nl_gd}    "vortex_gs": "Vortex",'
        assert anchor_bot in gd_text, f"Could not find grindor_cin_rotf in _BOT_NAMES in {gd_path}"
        gd_text = gd_text.replace(anchor_bot, repl_bot, 1)

        gd_path.write_text(gd_text, encoding="utf-8")
        print(f"[✓] Updated {gd_path} with vortex_gs")

# 6. Run export_payload.py
print("[*] Running export_payload.py...")
res = subprocess.run([sys.executable, str(ROOT / "Server" / "export_payload.py")], cwd=str(ROOT / "Server"), check=True)
print("[✓] export_payload.py completed successfully!")

print("\n[SUCCESS] All metadata, localization, server entries, and offline payload synced for Vortex strictly within TFTF-blender!")
