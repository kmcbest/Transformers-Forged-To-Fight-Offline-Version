#!/usr/bin/env python3
"""
TFTF Dual-Mode Combat Sandbox Analyzer (tools/sim/sim_match.py)
=================================================================
Mode 1 (--mode sim): Empirical Human-Calibrated Monte Carlo Simulation
  - Advances real fights with calibrated human P0 cadence, hit/block/evade rates,
    archetype playstyle mixes (melee_pressure / skirmish_ranged / artillery_heavy_dot / parry_counter),
    and per-fight random execution variance (+-15%~20%), reporting Mean + P10/P90 percentiles.
  - All hits, procs, DOTs, crits, evades, energy gain, and heals execute through sim_skills.dll.

Mode 2 (--mode dummy): Pure Offense Training Dummy Benchmark
  - Stationary 1x / 10x target (no blocking, no dodging, no counter-attacks, no defensive buffs).
  - Measures exact Hits-to-Kill, Seconds-to-Kill, DPS, and Direct vs DOT vs Crit breakdown
    while strictly earning SP energy from hits/skills. Supports --sp-pref sp1|sp2|sp3|compare.
"""
import argparse
import contextlib
import io
import random
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

SIM_DIR = Path(__file__).resolve().parent
REPO_ROOT = SIM_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from sim_server import g_engine, CURRENT_MATCHUP, trigger_onstart_phase, ALL_MODS

DT_MS = 100
MAX_FIGHT_MS = 360_000


def load_roster_meta():
    """Parse authentic 5/50 HP, ATK, class, and ranged-heavy flags from sim_roster_data.h."""
    roster = {}
    hdr = SIM_DIR / "sim_roster_data.h"
    if not hdr.exists():
        return roster
    # Match bot_id, bot_class, hp, atk, crit_chance, crit_damage, heavy_hits, {heavy_splits...}, {heavy_ranged[0]...}
    pat = re.compile(
        r'\{\s*"([^"]+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*[\d.]+f,\s*[\d.]+f,\s*'
        r'\d+,\s*\{[^}]+\},\s*\{\s*(\d+)'
    )
    for line in hdr.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.search(line)
        if m:
            roster[m.group(1)] = {
                "bot_class": int(m.group(2)),
                "hp": float(m.group(3)),
                "atk": float(m.group(4)),
                "heavy_is_ranged": int(m.group(5)) == 1,
            }
    return roster


ROSTER_META = load_roster_meta()


@dataclass
class Archetype:
    key: str
    title: str
    melee_weight: float      # Weight of initiating M-L-L-L-M / M-L-L-L-SP combo
    ranged_weight: float     # Weight of ranged poke (1-3 shots)
    heavy_weight: float      # Weight of Heavy attack
    sp_pref_default: str     # Preferred SP tier ("sp1" / "sp2" / "sp3")
    human_apm: float         # Expected P0 offensive cadence (acts/min)
    human_evade_rate: float  # Real-log calibrated probability P0 evades AI attack
    human_block_rate: float  # Probability P0 blocks AI attack when not evaded


ARCHETYPES = {
    "melee_pressure": Archetype(
        key="melee_pressure",
        title="近战压制流 (对标实战艾丽塔: 高近战连段+适量点射收招)",
        melee_weight=0.68,
        ranged_weight=0.22,
        heavy_weight=0.10,
        sp_pref_default="sp1",
        human_apm=66.0,
        human_evade_rate=0.64,
        human_block_rate=0.16,
    ),
    "skirmish_ranged": Archetype(
        key="skirmish_ranged",
        title="远近游击流 (对标实战阿尔茜: 高频后闪点射+近战拉扯)",
        melee_weight=0.45,
        ranged_weight=0.45,
        heavy_weight=0.10,
        sp_pref_default="sp1",
        human_apm=62.0,
        human_evade_rate=0.66,
        human_block_rate=0.20,
    ),
    "artillery_heavy_dot": Archetype(
        key="artillery_heavy_dot",
        title="远程重击DOT流 (对标电影铁皮/震荡波: 导弹重击+远程灼烧/震击)",
        melee_weight=0.32,
        ranged_weight=0.48,
        heavy_weight=0.20,
        sp_pref_default="sp2",
        human_apm=58.0,
        human_evade_rate=0.62,
        human_block_rate=0.22,
    ),
    "parry_counter": Archetype(
        key="parry_counter",
        title="防反重击流 (对标横炮/犀牛/音爆: 盾反破局+重击/背刺)",
        melee_weight=0.56,
        ranged_weight=0.24,
        heavy_weight=0.20,
        sp_pref_default="sp1",
        human_apm=60.0,
        human_evade_rate=0.65,
        human_block_rate=0.28,
    ),
}


def detect_archetype(bot_id: str) -> Archetype:
    meta = ROSTER_META.get(bot_id, {})
    heavy_ranged = meta.get("heavy_is_ranged", False)
    prefix = bot_id.split("_")[0]
    if prefix in ("blackout", "grindor"):
        # Blackout: Melee combo stacker for Infinite Fury + SP2 crit bleed
        base = ARCHETYPES["melee_pressure"]
        return Archetype(
            key=base.key, title="近战连击无尽怒火流 (蓄连击堆暴击+SP2流血爆发)",
            melee_weight=base.melee_weight, ranged_weight=base.ranged_weight,
            heavy_weight=base.heavy_weight, sp_pref_default="sp2",
            human_apm=base.human_apm, human_evade_rate=base.human_evade_rate,
            human_block_rate=base.human_block_rate,
        )
    if prefix in ("arcee", "jazz", "wheeljack", "prowl", "mirage", "bumblebee", "hound"):
        return ARCHETYPES["skirmish_ranged"]
    if prefix in ("ironhide", "shockwave", "acidstorm", "mixmaster", "thundercracker", "sunstorm", "hotlink", "ionstorm", "novastorm"):
        return ARCHETYPES["artillery_heavy_dot"]
    if prefix in ("sideswipe", "rhinox", "soundwave", "soundblaster", "barricade", "scorponok", "bonecrusher"):
        return ARCHETYPES["parry_counter"]
    if heavy_ranged and meta.get("bot_class", 0) in (3, 4):  # Tech / Demo with ranged heavy
        return ARCHETYPES["artillery_heavy_dot"]
    return ARCHETYPES["melee_pressure"]


@dataclass
class FightMetrics:
    winner: int = 0
    dur_s: float = 0.0
    p0_hp_end: float = 0.0
    p1_hp_end: float = 0.0
    p0_hp_pct: float = 0.0
    # Hit counters
    p0_hits_landed: int = 0
    p0_hits_blocked: int = 0
    p0_hits_evaded: int = 0
    p0_ranged_hits: int = 0
    p0_melee_hits: int = 0
    p0_heavy_hits: int = 0
    p0_sp_casts: dict = field(default_factory=lambda: {1: 0, 2: 0, 3: 0})
    p0_crits: int = 0
    # Incoming
    p1_hits_landed: int = 0
    p1_hits_blocked: int = 0
    p1_hits_evaded_by_p0: int = 0
    p1_sp_casts: dict = field(default_factory=lambda: {1: 0, 2: 0, 3: 0})
    # Damage / Heal decomposition
    p0_direct_dmg: float = 0.0   # includes hit direct damage (non-crit + crit base)
    p0_dot_dmg: float = 0.0      # bleed / shock / burn / acid DOT ticks
    p0_extra_dmg: float = 0.0    # instant skill extra damage (skill_deal_damage)
    p0_heal: float = 0.0
    p1_direct_dmg: float = 0.0
    p1_dot_dmg: float = 0.0
    p1_heal: float = 0.0


def collect_floaters(m: FightMetrics):
    for fl in g_engine.pop_floaters():
        pidx = int(fl.get("pidx", -1))
        ftype = int(fl.get("type", -1))
        val = float(fl.get("val", 0.0))
        txt = fl.get("text", "")
        if pidx not in (0, 1):
            continue
        if ftype in (0, 1):  # Damage inflicted onto pidx
            if pidx == 1:
                if txt == "DOT伤害":
                    m.p0_dot_dmg += val
                elif txt == "额外伤害":
                    m.p0_extra_dmg += val
                else:
                    m.p0_direct_dmg += val
                    if ftype == 1:
                        m.p0_crits += 1
                    if txt == "格挡":
                        m.p0_hits_blocked += 1
            else:
                if txt == "DOT伤害":
                    m.p1_dot_dmg += val
                else:
                    m.p1_direct_dmg += val
        elif ftype == 2:
            if pidx == 0:
                m.p0_heal += val
            else:
                m.p1_heal += val


def should_cast_sp(mana: float, sp_pref: str) -> int:
    if sp_pref == "sp3":
        return 3 if mana >= 3.0 else 0
    if sp_pref == "sp2":
        return 2 if mana >= 2.0 else 0
    if sp_pref == "sp1":
        return 1 if mana >= 1.0 else 0
    # Fallback mix: 70% SP1 / 25% SP2 / 5% SP3 threshold
    if mana >= 3.0:
        return 3
    if mana >= 2.0:
        return 2
    if mana >= 1.0:
        return 1
    return 0


def init_fight(p0_bot: str, p1_bot: str, p1_hp_mult: float, p1_atk_mult: float,
               strip_p1_def: bool = False):
    g_engine.set_authentic_mode(1)
    r0 = ROSTER_META.get(p0_bot, {"hp": 40000.0, "atk": 3000.0})
    r1 = ROSTER_META.get(p1_bot, {"hp": 40000.0, "atk": 3000.0})
    p0_hp = r0["hp"]
    p0_atk = r0["atk"]
    p1_hp = r1["hp"] * p1_hp_mult
    p1_atk = r1["atk"] * p1_atk_mult

    CURRENT_MATCHUP["p0_bot_id"] = p0_bot
    CURRENT_MATCHUP["p1_bot_id"] = p1_bot
    CURRENT_MATCHUP["p0_hp"] = p0_hp
    CURRENT_MATCHUP["p1_hp"] = p1_hp
    CURRENT_MATCHUP["p0_atk"] = p0_atk
    CURRENT_MATCHUP["p1_atk"] = p1_atk

    g_engine.init(p0_bot, p1_bot, p0_hp, p1_hp, p0_atk, p1_atk)
    with contextlib.redirect_stdout(io.StringIO()):
        trigger_onstart_phase()
    g_engine.tick(DT_MS)
    if strip_p1_def:
        # Remove common defensive start buffs for pure punching-bag Dummy benchmark
        for bkey in ("armor", "evade", "shield", "resist", "unstopp", "immune"):
            g_engine.remove_buff(1, bkey, 99)
    g_engine.pop_floaters()
    g_engine.pop_logs()
    return p0_hp, p1_hp


# ---------------------------------------------------------------------------
# Mode 1: Empirical Human-Calibrated Simulation (--mode sim)
# ---------------------------------------------------------------------------
def run_empirical_fight(p0_bot: str, p1_bot: str, archetype: Archetype, sp_pref: str,
                        ai_diff: str = "normal", p1_hp_mult: float = 1.0,
                        p1_atk_mult: float = 1.0, seed: int = 42,
                        enable_variance: bool = True) -> FightMetrics:
    rng = random.Random(seed)
    p0_hp0, p1_hp0 = init_fight(p0_bot, p1_bot, p1_hp_mult, p1_atk_mult, strip_p1_def=False)
    m = FightMetrics()

    # Apply realistic per-fight human & AI execution variance (+-15%~20%)
    if enable_variance:
        perf_scale = max(0.78, min(1.22, rng.gauss(1.0, 0.11)))
        ai_aggro = max(0.75, min(1.25, rng.gauss(1.0, 0.12)))
    else:
        perf_scale = 1.0
        ai_aggro = 1.0

    # Target calibrated rates derived from 4 live human matches:
    # - AI block rate against P0 openings: Normal ~20% (Fight 1-2 ~30% raw, ~20% post-punish), Hard ~16-25%
    # - AI evade rate against P0 openings: ~6% (Normal) / ~10% (Hard)
    ai_block_prob = (0.20 if ai_diff == "normal" else 0.22) * (1.0 / perf_scale)
    ai_evade_prob = (0.05 if ai_diff == "normal" else 0.09) * (1.0 / perf_scale)
    ai_block_prob = max(0.05, min(0.38, ai_block_prob))
    ai_evade_prob = max(0.02, min(0.18, ai_evade_prob))

    # Calibrated incoming P1 exchange attempts per minute:
    # Fight 1-2 Normal AI ~ 22-30 exchange attempts/min; Fight 3-4 Hard AI ~ 24-34 attempts/min
    p1_attempt_interval_ms = int((2600 if ai_diff == "normal" else 2000) / ai_aggro)
    p0_step_interval_ms = int((60_000.0 / (archetype.human_apm * perf_scale)))
    # Human defensive reaction calibrated from Fight 1-4 (evade ~64%, block ~18%, eaten unblocked ~18%)
    p0_evade_p = max(0.45, min(0.78, archetype.human_evade_rate * perf_scale))
    p0_block_p = max(0.08, min(0.32, archetype.human_block_rate))

    t_ms = 0
    next_p0_ms = 200
    next_p1_ms = 1100
    p0_combo_queue = []

    while t_ms < MAX_FIGHT_MS:
        st = g_engine.get_state()
        hp0, hp1 = float(st["p0"]["hp"]), float(st["p1"]["hp"])
        mana0, mana1 = float(st["p0"]["mana"]), float(st["p1"]["mana"])
        if hp0 <= 0.0 or hp1 <= 0.0:
            break

        # --- P0 Offense Timeline ---
        if g_engine.can_act(0):
            if p0_combo_queue:
                nt, act_t, hidx, is_last, dist = p0_combo_queue[0]
                if t_ms >= nt:
                    p0_combo_queue.pop(0)
                    g_engine.set_distance(dist)
                    if act_t > 100:
                        sp_t = act_t - 100
                        if mana0 >= float(sp_t):
                            g_engine.set_block(1, 0)
                            g_engine.exec_special(0, sp_t)
                            m.p0_sp_casts[sp_t] += 1
                            m.p0_hits_landed += 1
                    else:
                        if hidx == 0:
                            # Decide once per exchange whether AI blocks/evades this opening
                            ev_roll = rng.random()
                            if ev_roll < ai_evade_prob:
                                g_engine.dodge(1, 1)
                                m.p0_hits_evaded += 1
                                p0_combo_queue.clear()
                                next_p0_ms = t_ms + int(p0_step_interval_ms * 1.1)
                                continue
                            blk_open = 1 if (rng.random() < ai_block_prob) else 0
                            g_engine.set_block(1, blk_open)
                        dmg = g_engine.attack(0, act_t, hidx, is_last, -1)
                        if act_t == 8:
                            m.p0_ranged_hits += 1
                        elif act_t == 4:
                            m.p0_heavy_hits += 1
                        else:
                            m.p0_melee_hits += 1
                        if dmg > 0:
                            m.p0_hits_landed += 1
                        if is_last:
                            g_engine.set_block(1, 0)
            elif t_ms >= next_p0_ms:
                # Prefer SP if energy ready (real SP choice per sp_pref / mix)
                sp_choice = should_cast_sp(mana0, sp_pref)
                if sp_choice > 0 and rng.random() < 0.78:
                    g_engine.set_distance(4.0)
                    g_engine.set_block(1, 0)
                    if sp_choice < 3 and rng.random() < ai_evade_prob * 0.7:
                        g_engine.dodge(1, 1)
                        m.p0_hits_evaded += 1
                    else:
                        if sp_choice < 3 and rng.random() < ai_block_prob * 0.5:
                            g_engine.set_block(1, 1)
                        g_engine.exec_special(0, sp_choice)
                        m.p0_sp_casts[sp_choice] += 1
                        m.p0_hits_landed += 1
                    g_engine.set_block(1, 0)
                    next_p0_ms = t_ms + 1600
                else:
                    roll = rng.random()
                    if roll < archetype.ranged_weight:
                        # Ranged sequence: backdash + 2~3 ranged shots (matches Arcee/Ironhide style!)
                        n_shots = rng.choice((1, 2, 2, 3))
                        g_engine.dodge(0, 0)
                        for s_i in range(n_shots):
                            p0_combo_queue.append((t_ms + s_i * 220, 8, s_i, 1 if s_i == n_shots - 1 else 0, 10.0))
                        next_p0_ms = t_ms + n_shots * 240 + p0_step_interval_ms
                    elif roll < archetype.ranged_weight + archetype.heavy_weight:
                        # Heavy attack (auto-breaks AI block!)
                        g_engine.set_distance(2.5)
                        if rng.random() < ai_evade_prob * 1.2:
                            g_engine.dodge(1, 0)
                            m.p0_hits_evaded += 1
                        else:
                            g_engine.attack_start(0, 4)
                            g_engine.attack(0, 4, 0, 1, -1)
                            m.p0_heavy_hits += 1
                            m.p0_hits_landed += 1
                        next_p0_ms = t_ms + p0_step_interval_ms + 450
                    else:
                        # 5-hit melee combo M1-L1-L2-L3-M2 (or SP cancel on hit 4)
                        g_engine.dash(0)
                        p0_combo_queue = [
                            (t_ms + 0,   2, 0, 0, 2.0),
                            (t_ms + 220, 1, 0, 0, 2.0),
                            (t_ms + 440, 1, 1, 0, 2.0),
                            (t_ms + 660, 1, 2, 0, 2.0),
                            (t_ms + 900, 2, 1, 1, 2.0),
                        ]
                        next_p0_ms = t_ms + 1100 + int(p0_step_interval_ms * 0.5)

        # --- P1 AI Attempt (Filtered by calibrated Human P0 Evade / Block defense!) ---
        if t_ms >= next_p1_ms and g_engine.can_act(1):
            next_p1_ms = t_ms + int(p1_attempt_interval_ms * rng.uniform(0.75, 1.35))
            # Only fires when P0 isn't locking P1 down in active combo hits
            if not p0_combo_queue:
                if mana1 >= 2.0 and rng.random() < 0.55:
                    ai_sp = 2
                elif mana1 >= 1.0 and rng.random() < 0.50:
                    ai_sp = 1
                else:
                    ai_sp = 0

                def_roll = rng.random()
                if def_roll < p0_evade_p:
                    # Human backdashed / sidestepped cleanly! (still triggers dodge hook & attack_ended!)
                    ai_act = (16 if ai_sp == 1 else (32 if ai_sp == 2 else rng.choice((2, 8, 4))))
                    g_engine.dodge(0, rng.choice((0, 1)))
                    g_engine.fire_attack_ended(1, ai_act, 0, 0x0202, 0.0)
                    m.p1_hits_evaded_by_p0 += 1
                    if ai_sp > 0:
                        g_engine.set_mana(1, max(0.0, mana1 - ai_sp))  # whiffed AI SP spends AI bar
                        m.p1_sp_casts[ai_sp] += 1
                else:
                    blocked_by_p0 = 1 if (def_roll < p0_evade_p + p0_block_p) else 0
                    g_engine.set_block(0, blocked_by_p0)
                    if ai_sp > 0:
                        g_engine.exec_special(1, ai_sp)
                        m.p1_sp_casts[ai_sp] += 1
                        if blocked_by_p0 and ai_sp < 3:
                            m.p1_hits_blocked += 1
                        else:
                            m.p1_hits_landed += 1
                    else:
                        # Realistic 2~3 hit exchange or ranged shot
                        act_seq = rng.choice(([2, 1], [2, 1, 1], [8], [4] if ai_diff == "hard" else [2, 1]))
                        for k, a_t in enumerate(act_seq):
                            g_engine.attack(1, a_t, k, 1 if k == len(act_seq) - 1 else 0, -1)
                            if blocked_by_p0 and a_t != 4:
                                m.p1_hits_blocked += 1
                            else:
                                m.p1_hits_landed += 1
                    g_engine.set_block(0, 0)

        collect_floaters(m)
        g_engine.tick(DT_MS)
        t_ms += DT_MS
        collect_floaters(m)

    st_end = g_engine.get_state()
    hp0_e, hp1_e = float(st_end["p0"]["hp"]), float(st_end["p1"]["hp"])
    m.dur_s = t_ms / 1000.0
    m.p0_hp_end = hp0_e
    m.p1_hp_end = hp1_e
    m.p0_hp_pct = (hp0_e / p0_hp0) * 100.0
    m.winner = 0 if hp1_e <= 0.0 else (1 if hp0_e <= 0.0 else (0 if hp0_e / p0_hp0 >= hp1_e / p1_hp0 else 1))
    return m


# ---------------------------------------------------------------------------
# Mode 2: Stationary Punching-Bag Dummy Ceiling (--mode dummy)
# ---------------------------------------------------------------------------
def run_dummy_run(p0_bot: str, p1_bot: str, archetype: Archetype, sp_pref: str,
                  p1_hp_mult: float = 10.0, seed: int = 100) -> FightMetrics:
    """
    Opponent stands completely still: no blocking, no evading, no attacking,
    and start-of-fight defense buffs stripped. Measures pure Hits/Seconds-to-Kill.
    """
    random.seed(seed)
    p0_hp0, p1_hp0 = init_fight(p0_bot, p1_bot, p1_hp_mult, 1.0, strip_p1_def=True)
    m = FightMetrics()
    rng = random.Random(seed)

    t_ms = 0
    step_ms = 240  # Clean rhythmic input cadence on dummy
    next_act_ms = 0

    # Dummy rotation strictly tracks actual mana & archetype priority
    combo_idx = 0
    while t_ms < MAX_FIGHT_MS:
        st = g_engine.get_state()
        hp0 = float(st["p0"]["hp"])
        hp1 = float(st["p1"]["hp"])
        mana0 = float(st["p0"]["mana"])
        if hp0 <= 0.0 or hp1 <= 0.0:
            break

        if t_ms >= next_act_ms and g_engine.can_act(0):
            g_engine.set_block(1, 0)
            sp_choice = should_cast_sp(mana0, sp_pref)
            if sp_choice > 0:
                g_engine.set_distance(3.0)
                g_engine.exec_special(0, sp_choice)
                m.p0_sp_casts[sp_choice] += 1
                # Count real hits of SP from sp_choice execution
                m.p0_hits_landed += 1
                combo_idx = 0
                next_act_ms = t_ms + 1600
            else:
                # Choose dummy filler according to bot archetype
                roll = rng.random()
                if combo_idx == 0 and roll < archetype.ranged_weight * 0.8:
                    # Ranged burst
                    g_engine.set_distance(10.0)
                    g_engine.attack(0, 8, 0, 1, 0)
                    m.p0_ranged_hits += 1
                    m.p0_hits_landed += 1
                    next_act_ms = t_ms + 300
                elif combo_idx == 0 and roll < archetype.ranged_weight * 0.8 + archetype.heavy_weight:
                    g_engine.set_distance(2.5)
                    g_engine.attack_start(0, 4)
                    g_engine.attack(0, 4, 0, 1, 0)
                    m.p0_heavy_hits += 1
                    m.p0_hits_landed += 1
                    next_act_ms = t_ms + 900
                else:
                    # Standard 5-hit combo M1->L1->L2->L3->M2
                    g_engine.set_distance(2.0)
                    seq = ((2, 0, 0), (1, 0, 0), (1, 1, 0), (1, 2, 0), (2, 1, 1))
                    act_t, hidx, is_last = seq[combo_idx]
                    if combo_idx == 0:
                        g_engine.dash(0)
                    g_engine.attack(0, act_t, hidx, is_last, 0)
                    m.p0_melee_hits += 1
                    m.p0_hits_landed += 1
                    combo_idx = (combo_idx + 1) % 5
                    next_act_ms = t_ms + (420 if combo_idx == 0 else step_ms)

        collect_floaters(m)
        g_engine.tick(DT_MS)
        t_ms += DT_MS
        collect_floaters(m)

    st_end = g_engine.get_state()
    m.dur_s = t_ms / 1000.0
    m.p0_hp_end = float(st_end["p0"]["hp"])
    m.p1_hp_end = float(st_end["p1"]["hp"])
    m.winner = 0 if m.p1_hp_end <= 0.0 else 1
    return m


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return 0.0
    idx = int(round((len(sorted_vals) - 1) * pct))
    return sorted_vals[max(0, min(len(sorted_vals) - 1, idx))]


def print_empirical_summary(p0_bot, p1_bot, arch, sp_pref, ai_diff, p1_hp_mult, p1_atk_mult, runs):
    n = len(runs)
    wins = sum(1 for r in runs if r.winner == 0)
    durs = sorted(r.dur_s for r in runs)
    hp_pcts = sorted(r.p0_hp_pct for r in runs if r.winner == 0)
    tot_dmg = sorted((r.p0_direct_dmg + r.p0_dot_dmg + r.p0_extra_dmg) for r in runs)
    dps_list = sorted((r.p0_direct_dmg + r.p0_dot_dmg + r.p0_extra_dmg) / max(0.1, r.dur_s) for r in runs)

    r0 = ROSTER_META.get(p0_bot, {"hp": 40000, "atk": 3000})
    r1 = ROSTER_META.get(p1_bot, {"hp": 40000, "atk": 3000})
    mean_dir = statistics.mean(r.p0_direct_dmg for r in runs)
    mean_dot = statistics.mean(r.p0_dot_dmg for r in runs)
    mean_ext = statistics.mean(r.p0_extra_dmg for r in runs)
    mean_tot = max(1.0, mean_dir + mean_dot + mean_ext)

    print("==========================================================================")
    print(f"📊 【实战概率流】{p0_bot} vs {p1_bot} | N={n} | AI={ai_diff} | HPx{p1_hp_mult:.1f}")
    print(f"   打法流派: [{arch.key}] {arch.title} | SP偏好={sp_pref}")
    print(f"   面板: P0({r0['hp']:.0f}HP / {r0['atk']:.0f}ATK) vs P1({r1['hp']*p1_hp_mult:.0f}HP / {r1['atk']*p1_atk_mult:.0f}ATK)")
    print("--------------------------------------------------------------------------")
    print(f"  🏆 P0 胜率: {wins}/{n} ({wins*100.0/n:.1f}%)")
    if hp_pcts:
        print(f"  ❤️  胜场余血: 均值 {statistics.mean(hp_pcts):.1f}% | P10(险胜) {percentile(hp_pcts, 0.1):.1f}% | P90(轻松) {percentile(hp_pcts, 0.9):.1f}%")
    print(f"  ⏱️  局时 (秒): 均值 {statistics.mean(durs):.2f}s | P10 {percentile(durs, 0.1):.2f}s | P90 {percentile(durs, 0.9):.2f}s")
    print(f"  ⚡ P0 DPS: 均值 {statistics.mean(dps_list):.0f}/s | P10(非酋) {percentile(dps_list, 0.1):.0f}/s | P90(欧皇) {percentile(dps_list, 0.9):.0f}/s")
    print(f"  🎯 P0 输出构成 (均值 {mean_tot:.0f}): 直伤/暴击={mean_dir:.0f} ({mean_dir*100/mean_tot:.1f}%), "
          f"DOT={mean_dot:.0f} ({mean_dot*100/mean_tot:.1f}%), 附加技伤={mean_ext:.0f} ({mean_ext*100/mean_tot:.1f}%)")
    print(f"  🩸 P0 回复均值: {statistics.mean(r.p0_heal for r in runs):.0f} HP | 暴击均值: {statistics.mean(r.p0_crits for r in runs):.1f}次")
    print(f"  ⚔️  P0 出手均值: 近战={statistics.mean(r.p0_melee_hits for r in runs):.1f}, 远程={statistics.mean(r.p0_ranged_hits for r in runs):.1f}, "
          f"重击={statistics.mean(r.p0_heavy_hits for r in runs):.1f}, "
          f"SP1/2/3={statistics.mean(r.p0_sp_casts[1] for r in runs):.1f}/{statistics.mean(r.p0_sp_casts[2] for r in runs):.1f}/{statistics.mean(r.p0_sp_casts[3] for r in runs):.1f}, "
          f"被防={statistics.mean(r.p0_hits_blocked for r in runs):.1f}, 被闪={statistics.mean(r.p0_hits_evaded for r in runs):.1f}")
    print(f"  🛡️  P1 打中 P0 均值: 实中={statistics.mean(r.p1_hits_landed for r in runs):.1f}, 被挡={statistics.mean(r.p1_hits_blocked for r in runs):.1f}, "
          f"被P0躲掉={statistics.mean(r.p1_hits_evaded_by_p0 for r in runs):.1f}, AI放SP={statistics.mean(sum(r.p1_sp_casts.values()) for r in runs):.1f}, "
          f"P0总承伤={statistics.mean(r.p1_direct_dmg + r.p1_dot_dmg for r in runs):.0f}")
    print("==========================================================================")


def print_dummy_summary(p0_bot, p1_bot, arch, sp_pref, p1_hp_mult, runs):
    n = len(runs)
    r1 = ROSTER_META.get(p1_bot, {"hp": 40000})
    target_hp = r1["hp"] * p1_hp_mult
    total_hits = [r.p0_melee_hits + r.p0_ranged_hits + r.p0_heavy_hits + sum(r.p0_sp_casts.values()) for r in runs]
    durs = [r.dur_s for r in runs]
    dps = [(r.p0_direct_dmg + r.p0_dot_dmg + r.p0_extra_dmg) / max(0.1, r.dur_s) for r in runs]
    mean_dir = statistics.mean(r.p0_direct_dmg for r in runs)
    mean_dot = statistics.mean(r.p0_dot_dmg for r in runs)
    mean_ext = statistics.mean(r.p0_extra_dmg for r in runs)
    mean_tot = max(1.0, mean_dir + mean_dot + mean_ext)

    print(f"  🎯 [SP方案={sp_pref}] 打死 {target_hp:.0f} HP 木桩:")
    print(f"     最快/均值/最慢击杀步数: min={min(total_hits)} hits | mean={statistics.mean(total_hits):.1f} hits | P90={percentile(sorted(total_hits), 0.9):.0f} hits")
    print(f"     耗时与秒伤: mean={statistics.mean(durs):.2f}s (最快 {min(durs):.2f}s) | 均值 DPS={statistics.mean(dps):.0f}/s | P10~P90={percentile(sorted(dps),0.1):.0f}~{percentile(sorted(dps),0.9):.0f}/s")
    print(f"     伤害构成: 直伤/暴击={mean_dir:.0f} ({mean_dir*100/mean_tot:.1f}%), DOT={mean_dot:.0f} ({mean_dot*100/mean_tot:.1f}%), 技伤={mean_ext:.0f} ({mean_ext*100/mean_tot:.1f}%), 自疗={statistics.mean(r.p0_heal for r in runs):.0f}")
    print(f"     招式构成: 近战={statistics.mean(r.p0_melee_hits for r in runs):.1f}, 远程={statistics.mean(r.p0_ranged_hits for r in runs):.1f}, 重击={statistics.mean(r.p0_heavy_hits for r in runs):.1f}, "
          f"SP1/2/3={statistics.mean(r.p0_sp_casts[1] for r in runs):.1f}/{statistics.mean(r.p0_sp_casts[2] for r in runs):.1f}/{statistics.mean(r.p0_sp_casts[3] for r in runs):.1f}")


def main():
    ap = argparse.ArgumentParser(description="TFTF Dual-Mode Combat Sandbox Analyzer")
    ap.add_argument("--mode", choices=["sim", "dummy"], default="sim", help="sim=empirical MC, dummy=stationary target ceiling")
    ap.add_argument("--p0", default="nemesisprime_gs_voyager2015", help="P0 bot_id")
    ap.add_argument("--p1", default="ironhide_gs_kabam", help="P1 target/dummy bot_id")
    ap.add_argument("--style", choices=list(ARCHETYPES.keys()) + ["auto"], default="auto", help="Player playstyle archetype")
    ap.add_argument("--sp-pref", choices=["sp1", "sp2", "sp3", "auto", "compare"], default="auto", help="Preferred SP loop (or compare all 3 in dummy mode)")
    ap.add_argument("--ai", choices=["normal", "hard"], default="normal", help="AI pressure level in --mode sim")
    ap.add_argument("--p1-hp-mult", type=float, default=1.0, help="Target HP multiplier (default 1.0 in sim, recommend 10.0 in dummy)")
    ap.add_argument("--p1-atk-mult", type=float, default=1.0, help="Target ATK multiplier")
    ap.add_argument("--n", type=int, default=100, help="Number of simulated runs")
    ap.add_argument("--seed", type=int, default=42, help="Base RNG seed")
    args = ap.parse_args()

    arch = detect_archetype(args.p0) if args.style == "auto" else ARCHETYPES[args.style]

    if args.mode == "sim":
        sp_p = arch.sp_pref_default if args.sp_pref in ("auto", "compare") else args.sp_pref
        runs = [
            run_empirical_fight(
                args.p0, args.p1, arch, sp_p,
                ai_diff=args.ai, p1_hp_mult=args.p1_hp_mult, p1_atk_mult=args.p1_atk_mult,
                seed=args.seed + i,
            )
            for i in range(args.n)
        ]
        print_empirical_summary(args.p0, args.p1, arch, sp_p, args.ai, args.p1_hp_mult, args.p1_atk_mult, runs)
    else:
        hp_mult = args.p1_hp_mult if args.p1_hp_mult != 1.0 else 10.0
        prefs = ["sp1", "sp2", "sp3"] if args.sp_pref == "compare" else [arch.sp_pref_default if args.sp_pref == "auto" else args.sp_pref]
        r0 = ROSTER_META.get(args.p0, {"hp": 40000, "atk": 3000})
        print("==========================================================================")
        print(f"🪵 【极限木桩输出测算】P0={args.p0} (5/50 ATK={r0['atk']:.0f}) vs 木桩 {args.p1} (HPx{hp_mult:.1f}) | N={args.n}")
        print(f"   输出流派: [{arch.key}] {arch.title}")
        print("--------------------------------------------------------------------------")
        for sp_p in prefs:
            runs = [
                run_dummy_run(args.p0, args.p1, arch, sp_p, p1_hp_mult=hp_mult, seed=args.seed + i)
                for i in range(args.n)
            ]
            print_dummy_summary(args.p0, args.p1, arch, sp_p, hp_mult, runs)
        print("==========================================================================")


if __name__ == "__main__":
    main()
