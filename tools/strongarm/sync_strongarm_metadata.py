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

# Sources from extracted_apk (Prowl portraits)
p_large = ROOT / "extracted_apk" / "assets" / "assetpack" / "portraits_odr" / "portraits" / "portrait_prowl_gs_large.png"
if not p_large.exists():
    p_large = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\portraits_odr\portraits\portrait_prowl_gs_large.png")

p_small = ROOT / "extracted_apk" / "assets" / "assetpack" / "portraits_odr" / "portraits" / "portrait_prowl_gs_small.jpg"
if not p_small.exists():
    p_small = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\portraits_odr\portraits\portrait_prowl_gs_small.jpg")

p_quest = ROOT / "extracted_apk" / "assets" / "assetpack" / "questboard_odr" / "questboard" / "portrait_prowl_gs_quest.png"
if not p_quest.exists():
    p_quest = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\questboard_odr\questboard\portrait_prowl_gs_quest.png")

for src, dst_name in [
    (p_large, "portrait_strongarm_gs_large.png"),
    (p_large, "portrait_strongarm_large.png"),
    (p_large, "strongarm_gs.png"),
    (p_large, "strongarm.png"),
    (p_small, "portrait_strongarm_gs_small.jpg"),
    (p_small, "portrait_strongarm_small.jpg"),
    (p_quest, "portrait_strongarm_gs_quest.png"),
    (p_quest, "portrait_strongarm_quest.png"),
]:
    dst = redeco_dir / dst_name
    if src.exists():
        shutil.copy2(src, dst)
        print(f"[✓] Copied portrait: {dst_name}")
    else:
        print(f"[!] Warning: Portrait source not found: {src}")

# 2. Sync bot_names_zh.json (Strictly within ROOT repository)
strongarm_zh = {
    "en": "Strongarm",
    "zh": "铁腕",
    "faction": "汽车人",
    "note": "领袖的挑战·战术系",
    "desc": "来自《领袖之证/领袖的挑战》(RID2015) 的年轻热血汽车人警官。性格严谨刚正，一丝不苟地恪守警务条例，装备警用电击棍与重型霰弹枪，变形为越野警用巡逻皮卡。"
}

for zh_path in [
    ROOT / "bot_names_zh.json",
    ROOT / "Server" / "bot_names_zh.json",
]:
    if zh_path.exists():
        data = json.loads(zh_path.read_text(encoding="utf-8"))
        data["strongarm_gs"] = strongarm_zh
        zh_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
        print(f"[✓] Updated {zh_path}")

# 3. Sync custom_special_attacks.json & regenerate special_attacks_zh.h
sp_path = ROOT / "assets" / "xlate" / "custom_special_attacks.json"
sp_data = json.loads(sp_path.read_text(encoding="utf-8"))
strongarm_sp_entry = {
    "display_name": "铁腕",
    "specials": [
        {
            "name": "电击警棍制伏",
            "desc": "铁腕严正警告后疾速突刺，挥舞高压电击警棍连击瘫痪不法之徒。"
        },
        {
            "name": "执法霰弹轰鸣",
            "desc": "拔出重型战术霰弹枪近距离连续倾泻爆裂弹幕，击溃敌方防线。"
        },
        {
            "name": "警用能量锁链",
            "desc": "呼啸变形为越野巡逻车撞飞目标，随后掷出超高压能量手铐锁链将罪犯彻底锁死制裁。"
        }
    ]
}
sp_data.setdefault("bots", {})["strongarm"] = strongarm_sp_entry
sp_data["bots"]["strongarm_gs"] = strongarm_sp_entry
sp_path.write_text(json.dumps(sp_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[✓] Updated {sp_path}")

subprocess.run([sys.executable, str(ROOT / "tools" / "generate_special_attacks.py")], check=True)
print("[✓] Regenerated tools/nativehook/special_attacks_zh.h")

# 4. Update tools/nativehook/hook.c
hook_path = ROOT / "tools" / "nativehook" / "hook.c"
hook_text = hook_path.read_text(encoding="utf-8")
nl = "\r\n" if "\r\n" in hook_text else "\n"

if '"strongarm_gs"' not in hook_text:
    target_art = '    { "vortex_gs", "vortex_gs" },'
    repl_art = f'    {{ "vortex_gs", "vortex_gs" }},{nl}    {{ "strongarm_gs", "strongarm_gs" }},'
    assert target_art in hook_text, "Could not find vortex_gs in ART_BASE_MAP"
    hook_text = hook_text.replace(target_art, repl_art, 1)
    print("[✓] Added strongarm_gs to ART_BASE_MAP")

if 'strstr(k, "STRONGARM")' not in hook_text:
    target_vortex = (
        f'        if (strstr(k, "VORTEX") || strstr(k, "vortex") || strstr(k, "Vortex")) {{{nl}'
        f'            if (strstr(k, "BIO") || strstr(k, "desc") || strstr(k, "DESC") || strstr(k, "Bio")) {{{nl}'
        f'                return g_strnew("战车队阴险狂暴的突击兵与空中支援专家。旋风性格残忍好斗，狂热嗜杀，装备高频旋转离子切刃与重型导弹发射器，能够在半空化作杀戮旋风将一切敌人绞为碎片。");{nl}'
        f'            }}{nl}'
        f'            return g_strnew("旋风");{nl}'
        f'        }}'
    )
    strongarm_block = (
        f'{nl}        if (strstr(k, "STRONGARM") || strstr(k, "strongarm") || strstr(k, "Strongarm")) {{{nl}'
        f'            if (strstr(k, "BIO") || strstr(k, "desc") || strstr(k, "DESC") || strstr(k, "Bio")) {{{nl}'
        f'                return g_strnew("来自《领袖之证/领袖的挑战》(RID2015) 的年轻热血汽车人警官。性格严谨刚正，一丝不苟地恪守警务条例，装备警用电击棍与重型霰弹枪，变形为越野警用巡逻皮卡。");{nl}'
        f'            }}{nl}'
        f'            return g_strnew("铁腕");{nl}'
        f'        }}'
    )
    assert target_vortex in hook_text, "Could not find VORTEX block in hook_162"
    hook_text = hook_text.replace(target_vortex, target_vortex + strongarm_block, 1)
    print("[✓] Added strongarm localization to hook_162")

hook_path.write_text(hook_text, encoding="utf-8")

# 5. Update Server/gamedata.py (Strictly within ROOT repository)
gd_path = ROOT / "Server" / "gamedata.py"
if gd_path.exists():
    gd_text = gd_path.read_text(encoding="utf-8")
    nl_gd = "\r\n" if "\r\n" in gd_text else "\n"
    
    if '"strongarm_gs"' not in gd_text:
        # BASE_HEROES: Autobot Tactician 5-star
        anchor_hero = '    "ultramagnus_gs_leader":        ("autobot",    "tact", 5),'
        repl_hero = f'    "ultramagnus_gs_leader":        ("autobot",    "tact", 5),{nl_gd}    "strongarm_gs":                 ("autobot",    "tact", 5),'
        assert anchor_hero in gd_text, f"Could not find ultramagnus_gs_leader in BASE_HEROES in {gd_path}"
        gd_text = gd_text.replace(anchor_hero, repl_hero, 1)

        # _ART_BASE
        anchor_art = '    "ultramagnus_gs_leader": "ultram_gs",'
        repl_art = f'    "ultramagnus_gs_leader": "ultram_gs",{nl_gd}    "strongarm_gs": "strongarm_gs",'
        assert anchor_art in gd_text, f"Could not find ultramagnus_gs_leader in _ART_BASE in {gd_path}"
        gd_text = gd_text.replace(anchor_art, repl_art, 1)

        # _BOT_NAMES
        anchor_bot = '    "ultramagnus_gs_leader": "Ultra Magnus",'
        repl_bot = f'    "ultramagnus_gs_leader": "Ultra Magnus",{nl_gd}    "strongarm_gs": "Strongarm",'
        assert anchor_bot in gd_text, f"Could not find ultramagnus_gs_leader in _BOT_NAMES in {gd_path}"
        gd_text = gd_text.replace(anchor_bot, repl_bot, 1)

        gd_path.write_text(gd_text, encoding="utf-8")
        print(f"[✓] Updated {gd_path} with strongarm_gs")

# 5.5 Update Server/sp3_timings.json & regenerate tools/nativehook/bot_info.h
sp3_path = ROOT / "Server" / "sp3_timings.json"
if sp3_path.exists():
    sp3_data = json.loads(sp3_path.read_text(encoding="utf-8"))
    if "prowl_gs_deluxe2016" in sp3_data and "strongarm_gs" not in sp3_data:
        sa_sp3 = dict(sp3_data["prowl_gs_deluxe2016"])
        sa_sp3["notes"] = "铁腕 (Strongarm) - 警用皮卡 (借模警车Prowl)"
        sp3_data["strongarm_gs"] = sa_sp3
        sp3_path.write_text(json.dumps(sp3_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[✓] Added strongarm_gs to {sp3_path}")

sys.path.insert(0, str(ROOT / "Server"))
import gamedata as _gd
_gd.export_bot_info_header()
print("[✓] Regenerated tools/nativehook/bot_info.h with strongarm_gs")

# 6. Run export_payload.py
print("[*] Running export_payload.py...")
out_bin = ROOT / "build" / "payload_test.bin"
out_bin.parent.mkdir(parents=True, exist_ok=True)
res = subprocess.run([sys.executable, str(ROOT / "Server" / "export_payload.py"), "--out", str(out_bin)], cwd=str(ROOT), check=True)
print("[✓] export_payload.py completed successfully!")

print("\n[SUCCESS] All metadata, localization, server entries, and offline payload synced for Strongarm strictly within TFTF-blender!")
