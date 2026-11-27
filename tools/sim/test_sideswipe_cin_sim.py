#!/usr/bin/env python3
"""
电影横炮 (sideswipe_cin_rotf) 全套技能自动化门禁测试 (基于 sim_skills.dll)
==========================================================================
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SIM_DIR = Path(__file__).resolve().parent
REPO_ROOT = SIM_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from sim_server import g_engine


FAILS = 0


def check(cond: bool, msg: str):
    global FAILS
    if cond:
        print(f"  ✅ [PASS] {msg}")
    else:
        FAILS += 1
        print(f"  ❌ [FAIL] {msg}")


def get_buff_ids(pidx: int):
    st = g_engine.get_state()
    return [b["id"] for b in st[f"p{pidx}"]["buffs"]]


def get_buff_stacks(pidx: int, mod_id: str) -> int:
    st = g_engine.get_state()
    for b in st[f"p{pidx}"]["buffs"]:
        if b["id"] == mod_id:
            return int(b["stacks"])
    return 0


def reset_fight(p0="sideswipe_cin_rotf", p1="sharkticon_gs_brawler"):
    g_engine.set_authentic_mode(1)
    g_engine.init(p0, p1, 39343.0, 200000.0, 3366.0, 2500.0)
    g_engine.tick(100)
    g_engine.pop_floaters()
    g_engine.pop_logs()


def main():
    print("===========================================================================")
    print("🤖 电影横炮 (Sideswipe ROTF) 全套技能自动化门禁测试")
    print("===========================================================================")

    # --- TEST 1: 觉醒技“我真酷！”主动闪避叠层、M1必暴消耗与M2双重叠加 ---
    print("\n--- [TEST 1] 觉醒技“我真酷！”与 L4/M2 终结暴伤叠加 ---")
    reset_fight()
    # 模拟主动后闪/侧闪躲过敌人2次攻击
    g_engine.dodge(0, 0)
    g_engine.fire_attack_ended(1, 2, 0, 0x0202, 0.0)
    g_engine.tick(250)
    g_engine.dodge(0, 1)
    g_engine.fire_attack_ended(1, 8, 0, 0x0202, 0.0)
    g_engine.tick(100)
    stacks = get_buff_stacks(0, "sideswipe_cin_sig_cool")
    check(stacks == 2, f"主动闪避 2 次成功叠加 2 层 sideswipe_cin_sig_cool (actual={stacks})")

    # 直接以 M2 收招打中（测试 M2 自身 +180% 叠加 2层我真酷 +360% = +540% 暴伤, 共 6.90x）
    # 3366 * 0.40 * 6.90 = 9290.16 (向下取整约 9290)
    dmg_m2 = g_engine.attack(0, 2, 1, 1, 0)
    g_engine.tick(100)
    stacks_after = get_buff_stacks(0, "sideswipe_cin_sig_cool")
    check(dmg_m2 >= 9000, f"2层“我真酷”+ M2 必定暴击打出 ~6.90x 爆发伤害 (dmg={dmg_m2})")
    check(stacks_after == 0, f"M2 命中后清空所有“我真酷”层数 (after={stacks_after})")

    # 单独测 L4 (无招牌层数): 3366 * 0.20 * (1.50 + 1.80) = 2221.56
    reset_fight()
    dmg_l4 = g_engine.attack(0, 1, 3, 1, 0)
    check(2100 <= dmg_l4 <= 2350, f"L4 终结击无招牌时必定暴击并享受 +180% (3.30x) 暴伤 (dmg={dmg_l4})")

    # --- TEST 2: 前冲 / 重击远程 35% 穿透 + 100% 规避 ---
    print("\n--- [TEST 2] 前冲/重击远程穿透与 100% 规避门禁 ---")
    reset_fight()
    evaded_or_pierced = 0
    evade_callouts = 0
    for i in range(60):
        g_engine.dash(0)
        g_engine.pop_floaters()
        d = g_engine.attack(1, 8, 0, 1, 0)
        if d == 0:
            evaded_or_pierced += 1
        fls = g_engine.pop_floaters()
        if any(f.get("text", "") == "规避" for f in fls):
            evade_callouts += 1
        g_engine.tick(400)
    check(evaded_or_pierced == 60, f"前冲期间 60 次远程打击 100% 免疫 (35%穿透/65%规避, count={evaded_or_pierced}/60)")
    check(10 <= evade_callouts <= 55, f"前冲期间部分穿透(穿透规避)、未穿透触发普通“规避” (callout={evade_callouts}/60)")

    # --- TEST 3: 被动近战暴击流血(45%) 与 对流血目标 +24% 暴击率图标联动 ---
    print("\n--- [TEST 3] 近战暴击流血与对流血目标 +24% 暴击几率图标联动 ---")
    reset_fight()
    for _ in range(40):
        g_engine.attack(0, 2, 1, 1, 0)  # M2 必定暴击
        if "sideswipe_cin_crit_bleed" in get_buff_ids(1):
            break
    g_engine.tick(100)
    check("sideswipe_cin_crit_bleed" in get_buff_ids(1), "近战暴击成功施加 sideswipe_cin_crit_bleed")
    check("sideswipe_cin_bleed_crit_rate" in get_buff_ids(0), "对手流血时激活黄色 +24% 暴击率 (sideswipe_cin_bleed_crit_rate)")
    g_engine.tick(4500)
    check("sideswipe_cin_crit_bleed" not in get_buff_ids(1), "4秒后流血自然结束")
    check("sideswipe_cin_bleed_crit_rate" not in get_buff_ids(0), "对手流血结束后立即移除 +24% 暴击率图标")

    # --- TEST 4: SP1 85% 护甲驱散、SP2 暴击流血、SP 期间 +75% 暴伤与退出回收 ---
    print("\n--- [TEST 4] SP1/SP2/SP3 效果与技能期增益回收 ---")
    reset_fight()
    dispels = 0
    for _ in range(40):
        g_engine.remove_buff(1, "ironhide_sp2_armor_up", 99)
        g_engine.inject_buff(1, "ironhide_sp2_armor_up", 10.0, 1)
        g_engine.set_mana(0, 1.0)
        g_engine.exec_special(0, 1)
        if "ironhide_sp2_armor_up" not in get_buff_ids(1):
            dispels += 1
        g_engine.tick(2500)
    check(24 <= dispels <= 40, f"SP1 末击按 ~85% 概率驱散对手护甲增益 (dispels={dispels}/40)")
    check("sideswipe_cin_sp_crit_dmg" not in get_buff_ids(0), "SP 结束后立即清除 +75% 暴击伤害增益")
    check("sideswipe_cin_sp_anti_evade" not in get_buff_ids(0), "SP 结束后立即清除规避克制图标")

    # SP1 / SP2 期间强控对手 100% 近战规避无效（对标小黄蜂常驻近战规避）
    reset_fight(p0="sideswipe_cin_rotf", p1="bumblebee_dotm_deluxe2011")
    g_engine.inject_buff(1, "bumblebee_dodge_evade_melee", -1.0, 1)
    g_engine.set_mana(0, 2.0)
    sp2_dmg = g_engine.exec_special(0, 2)
    check(sp2_dmg > 0, f"SP2 全程克制规避，打中带近战规避buff的小黄蜂 (sp2_dmg={sp2_dmg})")

    # SP3 末击 100% 史诗级流血 (10s)
    reset_fight()
    g_engine.set_mana(0, 3.0)
    g_engine.exec_special(0, 3)
    check("sideswipe_cin_sp3_bleed" in get_buff_ids(1), "SP3 末击命中 100% 施加 10s 史诗级流血")

    print("\n===========================================================================")
    if FAILS == 0:
        print("✨ 恭喜！电影横炮 (Sideswipe ROTF) 全部门禁测试 PASSED！")
    else:
        print(f"❌ 有 {FAILS} 项测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
