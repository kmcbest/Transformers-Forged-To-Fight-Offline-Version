#!/usr/bin/env python3
"""
Export 5-star R5/L50 bot stats + real Heavy/SP1/SP2/SP3 hit counts, hit splits,
ranged flags, and animation durations from Server/gamedata.py + assetbundles
into tools/sim/sim_roster_data.h (LF line endings).
"""
import argparse
import json
import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "Server"))
import gamedata

CLASS_TO_INT = {
    "braw": 0,
    "warr": 1,
    "scou": 2,
    "tech": 3,
    "demo": 4,
    "tact": 5,
}


def load_moves_catalog():
    env_m = UnityPy.load(str(ROOT / "assets_redeco" / "moves.assetbundle"))
    by_name = {}
    by_pid = {}
    for obj in env_m.objects:
        if obj.type.name == "TextAsset":
            d = obj.read()
            by_name[d.m_Name] = d.m_Script
            by_pid[obj.path_id] = d.m_Name
    return by_name, by_pid


def find_bot_bundle(bid: str):
    p1 = ROOT / "assets_redeco" / f"{bid}.assetbundle"
    if p1.exists():
        return p1
    p2 = ROOT / "extracted_apk" / "assets" / "assetpack" / f"{bid}_odr" / f"{bid}.assetbundle"
    if p2.exists():
        return p2
    return None


def parse_move_events(move_script: str, default_hits=1, default_dur_ms=1500, default_ranged=False):
    if not move_script:
        return default_hits, [1.0 / default_hits] * default_hits, [1 if default_ranged else 0] * default_hits, default_dur_ms

    try:
        payload = json.loads(move_script)
    except Exception:
        return default_hits, [1.0 / default_hits] * default_hits, [1 if default_ranged else 0] * default_hits, default_dur_ms

    evs = payload.get("moves", {}).get("events", [])
    hit_frames = []
    max_frame = 0
    dur_ms = default_dur_ms

    for ev in evs:
        ev_type = ev.get("type", "")
        f = int(ev.get("f", 0) or 0)
        d = int(ev.get("d", 0) or 0)
        if f + d > max_frame:
            max_frame = f + d
        if ev_type == "AttackWindowMoveEvent" and d > 0:
            dur_ms = int(round(d * 1000.0 / 30.0))

        hd = ev.get("hd")
        if isinstance(hd, dict):
            dam = float(hd.get("dam", hd.get("m", 0.0)) or 0.0)
            at = int(hd.get("at", 1) or 1)
            is_ranged = 1 if ("Projectile" in ev_type or "Grenade" in ev_type or at == 2) else 0
            if dam > 0.0:
                hit_frames.append((f, dam, is_ranged))

    if max_frame > 0 and dur_ms == default_dur_ms:
        dur_ms = max(400, int(round(max_frame * 1000.0 / 30.0)))

    if not hit_frames:
        return default_hits, [1.0 / default_hits] * default_hits, [1 if default_ranged else 0] * default_hits, dur_ms

    hit_frames.sort(key=lambda x: x[0])
    if len(hit_frames) > 8:
        # Merge tail hits into slot 7 if any exotic move exceeds 8 hits
        head = hit_frames[:7]
        tail_dam = sum(x[1] for x in hit_frames[7:])
        tail_ranged = hit_frames[-1][2]
        hit_frames = head + [(hit_frames[7][0], tail_dam, tail_ranged)]

    total_dam = sum(x[1] for x in hit_frames)
    if total_dam <= 0.0:
        total_dam = float(len(hit_frames))
        splits = [1.0 / len(hit_frames)] * len(hit_frames)
    else:
        splits = [x[1] / total_dam for x in hit_frames]
    ranged_flags = [x[2] for x in hit_frames]
    return len(hit_frames), splits, ranged_flags, max(400, dur_ms)


def extract_bot_moves(bid: str, move_by_name: dict, move_by_pid: dict):
    bp = find_bot_bundle(bid)
    states = {}
    if bp is not None:
        try:
            env = UnityPy.load(str(bp))
            for obj in env.objects:
                if obj.type.name == "MonoBehaviour":
                    tree = obj.read_typetree()
                    if "_moves" in tree and len(tree["_moves"]) > 5:
                        for m in tree["_moves"]:
                            st = m.get("_animStateName", "")
                            mname = m.get("_name", "")
                            pid = (m.get("_asset") or {}).get("m_PathID", 0)
                            if mname not in move_by_name and pid in move_by_pid:
                                mname = move_by_pid[pid]
                            if st:
                                states[st] = mname
                        break
        except Exception as e:
            print(f"[WARN] Failed reading bundle {bp}: {e}")

    def resolve(state_key, def_hits=1, def_dur=1500, def_ranged=False):
        mname = states.get(state_key, "")
        script = move_by_name.get(mname, "")
        return parse_move_events(script, def_hits, def_dur, def_ranged)

    heavy = resolve("Base.HeavyAttack", 1, 1100, False)
    sp1 = resolve("Base.SpecialAttack01", 2, 1800, False)
    sp2 = resolve("Base.SpecialAttack02", 3, 2400, False)
    sp3 = resolve("Base.SpecialAttack03", 1, 4500, False)
    return heavy, sp1, sp2, sp3


def fmt_float_arr(arr, size=8):
    padded = list(arr) + [0.0] * (size - len(arr))
    return "{ " + ", ".join(f"{x:.4f}f" for x in padded[:size]) + " }"


def fmt_int_arr(arr, size=8):
    padded = list(arr) + [0] * (size - len(arr))
    return "{ " + ", ".join(str(int(x)) for x in padded[:size]) + " }"


def classify_mod_kind(mod: dict, mod_id: str) -> int:
    t = str(mod.get("t", "") or "").lower()
    ta = str(mod.get("ta", "self") or "self").lower()
    mt = str(mod.get("mt", "buff") or "buff").lower()
    if t == "crit_damage":
        return 1  # SMOD_CRIT_DAMAGE
    if t == "crit_rate":
        return 3 if (ta == "opponent" or mt == "debuff") else 2
    if t == "crit_rate_debuff":
        return 3  # SMOD_CRIT_RATE_DEBUFF
    if t in ("attack", "attack_buff", "attack_debuff", "attack_rating"):
        return 4  # SMOD_ATTACK_MOD
    if t in ("armor", "armor_up"):
        return 5  # SMOD_ARMOR_UP
    if t == "armor_break":
        return 6  # SMOD_ARMOR_BREAK
    if t == "dmg_bleed" or (t == "debuff" and "bleed" in mod_id):
        return 7  # SMOD_DOT_BLEED
    if t == "dmg_burn":
        return 8  # SMOD_DOT_BURN
    if t == "dmg_shock":
        return 9  # SMOD_DOT_SHOCK
    if t == "acrolight_bomb" or "acid" in mod_id:
        return 10  # SMOD_DOT_ACID
    if t in ("special_damage", "special_damage_buff"):
        return 11  # SMOD_SPECIAL_DMG
    if t == "ranged_buff":
        return 12  # SMOD_RANGED_BUFF
    if t in ("power_rate", "power_rate_buff", "power_rate_debuff", "power_gain"):
        return 13  # SMOD_POWER_RATE
    return 0


def parse_trigger_mask(trs: list) -> int:
    mask = 0
    mapping = {
        "onHit": 1 << 0,
        "onCrit": 1 << 1,
        "onBlocked": 1 << 2,
        "onHeavyHit": 1 << 3,
        "onSpecial1Activate": 1 << 4,
        "onSpecial2Activate": 1 << 5,
        "onSpecial3Activate": 1 << 6,
        "onSpecialActivate": (1 << 4) | (1 << 5) | (1 << 6),
        "onSpecial1Hit": 1 << 8,
        "onSpecial2Hit": 1 << 9,
        "onSpecial3Hit": 1 << 10,
        "onPreDamage": 1 << 11,
    }
    for tr in (trs or []):
        mask |= mapping.get(str(tr), 0)
    return mask


def parse_level_scope(trs_str: str):
    if not trs_str:
        return 0x7F, 0
    is_state = 1 if "state=" in trs_str else 0
    if "level=" not in trs_str:
        return 0x7F, is_state
    lvl = 0
    low = trs_str.lower()
    if "light" in low:
        lvl |= (1 << 0)
    if "medium" in low:
        lvl |= (1 << 1)
    if "heavy" in low:
        lvl |= (1 << 2)
    if "ranged" in low:
        lvl |= (1 << 3)
    if "special1" in low:
        lvl |= (1 << 4)
    if "special2" in low:
        lvl |= (1 << 5)
    if "special3" in low:
        lvl |= (1 << 6)
    return (lvl if lvl > 0 else 0x7F), is_state


def export_mods_header():
    from abilities.registry import load_all_bots, _BOT_REGISTRY
    load_all_bots()

    entries = []
    seen = set()
    for bid in sorted(_BOT_REGISTRY.keys()):
        builder = _BOT_REGISTRY[bid]["builder"]
        try:
            r1 = builder(base_hp=10000.0, base_atk=1000.0)
            r2 = builder(base_hp=10000.0, base_atk=2000.0)
        except Exception:
            continue
        m1 = r1[0] if isinstance(r1, (tuple, list)) else r1
        m2 = r2[0] if isinstance(r2, (tuple, list)) else r2
        _, roster_atk = gamedata.base_stats(bid, 5, 50)
        if roster_atk <= 0:
            roster_atk = 3000

        for mid, mod in m1.items():
            if mid in seen:
                continue
            seen.add(mid)
            kind = classify_mod_kind(mod, mid)
            tr_mask = parse_trigger_mask(mod.get("tr", []))
            lvl_mask, is_state = parse_level_scope(str(mod.get("trs", "") or ""))
            is_dot = kind in (7, 8, 9, 10)
            raw_m1 = float(mod.get("m", 0.0) or 0.0)
            raw_m2 = float((m2.get(mid) or {}).get("m", raw_m1) or raw_m1)

            if is_dot:
                # Normalize DOT total damage into fraction of attacker ATK
                if raw_m1 > 0.0 and abs(raw_m2 - raw_m1 * 2.0) < abs(raw_m2 - raw_m1):
                    mag = raw_m1 / 1000.0
                else:
                    mag = abs(raw_m1) / float(roster_atk)
            else:
                mag = raw_m1

            st = int(mod.get("st", 1) or 1)
            ta = 1 if str(mod.get("ta", "self")).lower() == "opponent" else 0
            is_deb = 1 if str(mod.get("mt", "buff")).lower() == "debuff" else 0
            dur = float(mod.get("d", -1.0) or -1.0)
            chance = float(mod.get("c", 1.0) or 1.0)
            entries.append((mid, bid, kind, st, ta, is_deb, mag, dur, chance, tr_mask, lvl_mask, is_state))

    lines = [
        "// Auto-generated by tools/sim/export_sim_roster.py. DO NOT EDIT DIRECTLY.",
        "#ifndef SIM_MODS_DATA_H",
        "#define SIM_MODS_DATA_H",
        "#include <stdint.h>",
        "",
        "#define SMOD_OTHER            0",
        "#define SMOD_CRIT_DAMAGE      1",
        "#define SMOD_CRIT_RATE        2",
        "#define SMOD_CRIT_RATE_DEBUFF 3",
        "#define SMOD_ATTACK_MOD       4",
        "#define SMOD_ARMOR_UP         5",
        "#define SMOD_ARMOR_BREAK      6",
        "#define SMOD_DOT_BLEED        7",
        "#define SMOD_DOT_BURN         8",
        "#define SMOD_DOT_SHOCK        9",
        "#define SMOD_DOT_ACID        10",
        "#define SMOD_SPECIAL_DMG     11",
        "#define SMOD_RANGED_BUFF     12",
        "#define SMOD_POWER_RATE      13",
        "",
        "#define STRIG_ON_HIT          (1u << 0)",
        "#define STRIG_ON_CRIT         (1u << 1)",
        "#define STRIG_ON_BLOCKED      (1u << 2)",
        "#define STRIG_ON_HEAVY_HIT    (1u << 3)",
        "#define STRIG_ON_SP1_ACTIVATE (1u << 4)",
        "#define STRIG_ON_SP2_ACTIVATE (1u << 5)",
        "#define STRIG_ON_SP3_ACTIVATE (1u << 6)",
        "#define STRIG_ON_SP1_HIT      (1u << 8)",
        "#define STRIG_ON_SP2_HIT      (1u << 9)",
        "#define STRIG_ON_SP3_HIT      (1u << 10)",
        "#define STRIG_ON_PRE_DAMAGE   (1u << 11)",
        "",
        "#define SLVL_LIGHT   (1u << 0)",
        "#define SLVL_MEDIUM  (1u << 1)",
        "#define SLVL_HEAVY   (1u << 2)",
        "#define SLVL_RANGED  (1u << 3)",
        "#define SLVL_SP1     (1u << 4)",
        "#define SLVL_SP2     (1u << 5)",
        "#define SLVL_SP3     (1u << 6)",
        "#define SLVL_ALL     0x7Fu",
        "",
        "typedef struct {",
        "    const char* mod_id;",
        "    const char* owner_bot_id;",
        "    int kind;",
        "    int max_stacks;",
        "    int target_opp;",
        "    int is_debuff;",
        "    float magnitude;",
        "    float duration_s;",
        "    float chance;",
        "    uint32_t tr_mask;",
        "    uint32_t lvl_mask;",
        "    int is_state_only;",
        "} SimModMeta;",
        "",
        "static const SimModMeta SIM_MODS[] = {",
    ]
    for e in entries:
        mid, bid, kind, st, ta, is_deb, mag, dur, ch, tm, lm, st_only = e
        lines.append(
            f'    {{ "{mid}", "{bid}", {kind}, {st}, {ta}, {is_deb}, {mag:.4f}f, {dur:.2f}f, {ch:.3f}f, 0x{tm:04X}u, 0x{lm:02X}u, {st_only} }},'
        )
    lines.append("};")
    lines.append(f"#define NUM_SIM_MODS {len(entries)}")
    lines.append("")
    lines.append("#endif // SIM_MODS_DATA_H")
    lines.append("")

    out_path = ROOT / "tools" / "sim" / "sim_mods_data.h"
    out_path.write_bytes(("\n".join(lines)).encode("utf-8"))
    print(f"Wrote {out_path} ({len(entries)} StatMods across {len(_BOT_REGISTRY)} bots)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mods-only", action="store_true", help="Only regenerate sim_mods_data.h quickly")
    args = ap.parse_args()

    export_mods_header()
    if args.mods_only:
        return

    move_by_name, move_by_pid = load_moves_catalog()
    bots = sorted(gamedata.ROSTER.keys())
    print(f"Loaded {len(move_by_name)} moves; exporting {len(bots)} bots...")

    lines = [
        "// Auto-generated by tools/sim/export_sim_roster.py. DO NOT EDIT DIRECTLY.",
        "#ifndef SIM_ROSTER_DATA_H",
        "#define SIM_ROSTER_DATA_H",
        "",
        "typedef struct {",
        "    const char* bot_id;",
        "    int bot_class;      // 0=braw, 1=warr, 2=scou, 3=tech, 4=demo, 5=tact",
        "    int hp;",
        "    int atk;",
        "    float crit_chance;",
        "    float crit_damage;",
        "    int heavy_hits;",
        "    float heavy_splits[8];",
        "    int heavy_ranged[8];",
        "    int heavy_dur_ms;",
        "    int sp1_hits;",
        "    float sp1_splits[8];",
        "    int sp1_ranged[8];",
        "    int sp1_dur_ms;",
        "    int sp2_hits;",
        "    float sp2_splits[8];",
        "    int sp2_ranged[8];",
        "    int sp2_dur_ms;",
        "    int sp3_hits;",
        "    float sp3_splits[8];",
        "    int sp3_dur_ms;",
        "} SimRosterEntry;",
        "",
        "static const SimRosterEntry SIM_ROSTER[] = {",
    ]

    extracted_bundles = 0
    for bid in bots:
        faction, klass, star = gamedata.ROSTER[bid]
        hp, atk = gamedata.base_stats(bid, 5, 50)
        cls_st = gamedata._CLASS_STATS.get(klass, {"crit_chance": 0.16, "crit_damage": 1.50})
        cc = cls_st["crit_chance"]
        cd = cls_st["crit_damage"]
        if bid in gamedata._BASE_STATS_OVERRIDE:
            cc = gamedata._BASE_STATS_OVERRIDE[bid].get("crit_chance", cc)
            cd = gamedata._BASE_STATS_OVERRIDE[bid].get("crit_damage", cd)

        if find_bot_bundle(bid) is not None:
            extracted_bundles += 1
        heavy, sp1, sp2, sp3 = extract_bot_moves(bid, move_by_name, move_by_pid)
        c_int = CLASS_TO_INT.get(klass, 5)

        lines.append(
            f'    {{ "{bid}", {c_int}, {hp}, {atk}, {cc:.2f}f, {cd:.2f}f, '
            f'{heavy[0]}, {fmt_float_arr(heavy[1])}, {fmt_int_arr(heavy[2])}, {heavy[3]}, '
            f'{sp1[0]}, {fmt_float_arr(sp1[1])}, {fmt_int_arr(sp1[2])}, {sp1[3]}, '
            f'{sp2[0]}, {fmt_float_arr(sp2[1])}, {fmt_int_arr(sp2[2])}, {sp2[3]}, '
            f'{sp3[0]}, {fmt_float_arr(sp3[1])}, {sp3[3]} }},'
        )

    lines.append("};")
    lines.append(f"#define NUM_SIM_MODS_ROSTER {len(bots)}")
    lines.append(f"#define NUM_SIM_ROSTER {len(bots)}")
    lines.append("")
    lines.append("#endif // SIM_ROSTER_DATA_H")
    lines.append("")

    out_path = ROOT / "tools" / "sim" / "sim_roster_data.h"
    out_path.write_bytes(("\n".join(lines)).encode("utf-8"))
    print(f"Wrote {out_path} ({len(bots)} bots, {extracted_bundles} bundles parsed)")


if __name__ == "__main__":
    main()
