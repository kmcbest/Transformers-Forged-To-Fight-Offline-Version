#!/usr/bin/env python3
"""
Authored offline game data for the TFTF revival.

WHAT THIS IS
------------
This module is the single, hand-authored source of the server-side content that
Kabam used to stream to the client and that shut down with their servers in 2020.
None of the original balance data survived, so everything here is ORIGINAL work:
the class/faction assignments, the star rarities, every stat number, and the whole
combat balance table were invented for this offline revival, not copied from Kabam.

It only produces DATA in the JSON shapes the unmodified client already parses (the
same shapes proven to work in Server/responses/). It contains no game assets, no
copyrighted binaries, and no recovered Kabam data -- it references asset IDs that
already ship inside the user's own copy of the APK, and fills them with fresh numbers.

WHY IT IS SEPARATE
------------------
Keeping the content here (instead of inline in fakeserver.py or scattered across
hand-edited JSON files) makes the roster and balance easy to extend the way the
README describes: add a row, run `python gamedata.py`, verify against the client,
repeat. `build_responses()` regenerates the roster-driven response files and merges
the authored combat tuning into account data so they can never drift out of sync.

The character id list is taken from re_notes/ASSET_INVENTORY.txt -- these are the
bundles that already ship in the app, so their art exists; only the numbers were
missing. See COMPLIANCE.md for the full rationale.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RESP_DIR = os.path.join(HERE, "responses")

# DIAGNOSTIC ONLY — keep the default at 0. PlayerAttributes.Init@0xDAB16C initializes
# starting mana as maxMana * mana_start. Setting TFTF_DIAG_MANA_START=1 therefore makes
# the first combat frame distinguish maxMana == 0 (still empty) from a zero per-hit gain
# (full). This is not gameplay tuning; all authored balance values in this revival remain
# original inventions, never recovered Kabam data.
_DIAG_MANA_START = max(0, min(1, int(os.environ.get("TFTF_DIAG_MANA_START", "0"))))

# Wire `mana_gain` -> BCGAttributeDataBase.ManaGain@0x54 -> PlayerAttributes._powerGainRate
# @0x138 (seeded in PlayerAttributes.Init@0xDAB16C, loads @0xDABE00/0xDABE08). Per-hit mana
# is `attackValues[*].m * HitData.Mana * powerGainRate` (fmul @0xDADC80/0xDADC84), so a
# missing or zero mana_gain multiplies every special-attack meter gain to zero for both
# fighters. 1.0 means the original authored attackValues[*].m for this revival are taken at
# face value; it is not recovered Kabam data.
_MANA_GAIN_RATE = 1.0

# The six combat classes are a factual part of the game's structure. Which class a
# given bot belongs to on Kabam's servers is lost data, so the assignments below are
# an original, self-consistent reconstruction, not the historical values.
CLASSES = ("braw", "tact", "scou", "demo", "warr", "tech")

# CDN host the working login-data response points at. Kept identical to the proven
# Server/responses/GET__bcg_getLoginData.json so asset resolution behaves the same.
CDN = "https://tform-0901-hzlhiniyfcwf.tf-cdn.net"

# ---------------------------------------------------------------------------
# Roster.  id -> (faction, class, star)
#   faction : "autobot" | "decepticon"  (maps to the `gen` field)
#   class   : one of CLASSES
#   star    : 1..5 rarity, drives the authored stat curve below
#
# The ids are the asset-bundle names from ASSET_INVENTORY.txt. Faction is set to the
# character's well-known allegiance; class and star are an ORIGINAL assignment made
# for this revival so the roster is playable and internally balanced.
# ---------------------------------------------------------------------------
ROSTER = {
    # --- First-time-experience bots (intro fight: Optimus vs Starscream) ---
    "fte_optimus_gs_t3":            ("autobot",    "tact", 5),
    "fte_stars_gs_t3":              ("decepticon", "tact", 5),

    # --- Autobots ---
    "arcee_gs_deluxe2014":          ("autobot",    "warr", 5),
    "blaster_gs_leader2016":        ("autobot",    "tech", 5),
    "bumblebee_cin_dotm":           ("autobot",    "tact", 5),
    "bumblebee_gs_kabam":           ("autobot",    "scou", 5),
    "cheetor_bw_transmetal":        ("autobot",    "scou", 5),
    "chromia_gs_kabam":             ("autobot",    "warr", 5),
    "cliffjumper_gs_kabam":         ("autobot",    "demo", 5),
    "dinobot_bw_kabam":             ("autobot",    "tact", 5),
    "drift_cin_aoe":                ("autobot",    "warr", 5),
    "grimlock_gs_mp08":             ("autobot",    "braw", 5),
    "hotrod_cin_tlk":               ("autobot",    "warr", 5),
    "hound_cin_tlk":                ("autobot",    "warr", 5),
    "ironhide_cin_rotf":            ("autobot",    "demo", 5),
    "ironhide_gs_kabam":            ("autobot",    "braw", 5),
    "jazz_gs_twm05":                ("autobot",    "scou", 5),
    "jetfire_gs_leader2014":        ("autobot",    "tech", 5),
    "mirage_gs_deluxe2016":         ("autobot",    "tech", 5),
    "optimusprimal_bw_mp32":        ("autobot",    "braw", 5),
    "optimusprime_cin_tf":          ("autobot",    "braw", 5),
    "optimusprime_sg_voyager2015":  ("autobot",    "braw", 5),
    "prowl_gs_deluxe2016":          ("autobot",    "scou", 5),
    "ratchet_gs_kabam":             ("autobot",    "tech", 5),
    "rhinox_gs_voyager2014":        ("autobot",    "tech", 5),
    "rodimusprime_gs_mp09":         ("autobot",    "tact", 5),
    "sideswipe_gs":                 ("autobot",    "scou", 5),
    "starsaber_gs_leader2014":      ("autobot",    "tact", 5),
    "sunstreaker_gs_deluxe2008":    ("autobot",    "braw", 5),
    "ultramagnus_gs_leader":        ("autobot",    "tact", 5),
    "wheeljack_gs_mp20":            ("autobot",    "tech", 5),
    "windblade_gs":                 ("autobot",    "warr", 5),

    # --- Decepticons ---
    "acidstorm_gs_leader2015":      ("decepticon", "tech", 5),
    "barricade_cin_dotm":           ("decepticon", "scou", 5),
    "bitstream_gs_leader2015":      ("decepticon", "tech", 5),
    "bludgeon_gs_rd20":             ("decepticon", "warr", 5),
    "bonecrusher_cin_rotf":         ("decepticon", "warr", 5),
    "cyclonus_gs_uw06":             ("decepticon", "tact", 5),
    "deadend_gs_deluxe2015":        ("decepticon", "demo", 5),
    "dirge_gs_deluxe2008":          ("decepticon", "warr", 5),
    "galvatron_gs_voyager2016":     ("decepticon", "demo", 5),
    "grindor_cin_rotf":             ("decepticon", "braw", 5),
    "hotlink_gs_leader2015":        ("decepticon", "braw", 5),
    "ionstorm_gs_leader2015":       ("decepticon", "tact", 5),
    "kickback_gs_kabam":            ("decepticon", "scou", 5),
    "megatron_cin_rotf":            ("decepticon", "demo", 5),
    "megatron_gs_leader2015":       ("decepticon", "tact", 5),
    "megatronus_gs_kabam":          ("decepticon", "demo", 5),
    "mixmaster_cin_rotf":           ("decepticon", "demo", 5),
    "motormaster_gs_voyager2015":   ("decepticon", "braw", 5),
    "necrotronus_gs_kabam":         ("decepticon", "warr", 5),
    "nemesisprime_gs_voyager2015":  ("decepticon", "tact", 5),
    "novastorm_gs_leader2015":      ("decepticon", "demo", 5),
    "ramjet_gs_deluxe2008":         ("decepticon", "demo", 5),
    "scorponok_bw_kabam":           ("decepticon", "warr", 5),
    "shockwave_gs":                 ("decepticon", "tech", 5),
    "skywarp_gs_leader2015":        ("decepticon", "tech", 5),
    "slipstream_gs":                ("decepticon", "scou", 5),
    "soundblaster_gs_mp13b":        ("decepticon", "demo", 5),
    "soundwave_gs":                 ("decepticon", "tech", 5),
    "sunstorm_gs_leader2015":       ("decepticon", "warr", 5),
    "thundercracker_gs_leader2015": ("decepticon", "braw", 5),
    "thrust_gs_deluxe2008":         ("decepticon", "scou", 5),
    "tantrum_gs_kabam":             ("decepticon", "braw", 5),
    "waspinator_gs_deluxe":         ("decepticon", "demo", 5),

    # --- Sharkticons (generic enemy fodder; low rarity) ---
    "sharkticon_gs_kabam":          ("decepticon", "braw", 1),
    "sharkticon_gs_brawler":        ("decepticon", "braw", 1),
    "sharkticon_gs_demolition":     ("decepticon", "demo", 1),
    "sharkticon_gs_scout":          ("decepticon", "scou", 1),
    "sharkticon_gs_tactician":      ("decepticon", "tact", 1),
    "sharkticon_gs_tech":           ("decepticon", "tech", 1),
    "sharkticon_gs_warrior":        ("decepticon", "warr", 1),
}

# Which bots the offline player owns at boot. For a preservation sandbox we grant the
# ENTIRE roster so every screen (roster grid, hero details, team select) has content.
OWNED = list(ROSTER)

# ---------------------------------------------------------------------------
# Authored stat curve.  All ORIGINAL, all invented for this revival.
# ---------------------------------------------------------------------------
# Per-class flavour: brawlers tanky, warriors hit hard, scouts glassy, etc.
# (multipliers applied on top of the star base). Original balance.
_CLASS_MOD = {
    "braw": (1.25, 0.90),  # (hp_mult, atk_mult)
    "tact": (1.00, 1.00),
    "scou": (0.85, 1.20),
    "demo": (1.10, 1.05),
    "warr": (0.95, 1.15),
    "tech": (1.05, 0.95),
}

# Star rarity base line (level 1, rank 1). Original.
_STAR_BASE = {
    1: (2200, 210),
    2: (3400, 300),
    3: (5200, 430),
    4: (7800, 610),
    5: (11500, 850),
}


def base_stats(bid, rank=1, level=1):
    """Authored HP/attack for a bot at a given rank/level. Pure, deterministic,
    and original. Higher rank and level scale monotonically so upgrades feel real."""
    faction, klass, star = ROSTER.get(bid, ("decepticon", "tact", 1))
    hp0, atk0 = _STAR_BASE.get(star, _STAR_BASE[1])
    hpm, atkm = _CLASS_MOD.get(klass, (1.0, 1.0))
    # rank multiplies, level adds a per-level slice (~9% of base per 10 levels).
    rank_mult = 1.0 + 0.35 * (max(1, rank) - 1)
    level_add = (max(1, level) - 1) / 100.0
    hp = int(hp0 * hpm * rank_mult * (1.0 + level_add))
    atk = int(atk0 * atkm * rank_mult * (1.0 + level_add))
    return hp, atk


# msa values from the proven Server/responses/GET__bcg_getLoginData.json. The intro
# fight was verified working with these exact numbers, so we preserve them rather than
# let the authored curve change proven-working entries.
_MSA_OVERRIDE = {
    "bumblebee_gs_kabam": 3,
    "fte_optimus_gs_t3": 3,
    "fte_stars_gs_t3": 3,
}


def max_special_attacks(bid, star):
    """How many special attacks a bot can charge. Proven entries keep their verified
    value; everything else uses the authored rarity curve."""
    if bid in _MSA_OVERRIDE:
        return _MSA_OVERRIDE[bid]
    return 1 if star <= 1 else (2 if star <= 3 else 3)


# Special-attack ("transform") damage ratios -> blueprint s1/s2/s3, parsed into
# BCGBlueprintBase.Special1Damage/Special2Damage/Special3Damage. These are on the same
# scale as the normal-attack `attackValues` percents (see build_attack_values): a Heavy
# is 1.0, Medium 0.60, Light 0.35. When a bot transforms it fires one of these specials,
# so each ratio must clearly exceed a regular punch/kick for the transform to read as the
# hardest hit. The proven response shipped a flat placeholder 1.0/1.0/1.0, which made a
# transform land no harder than a Heavy and only ~1.7x a Medium -- the "transforms don't
# hit harder" report. The escalating curve below keeps SP1 < SP2 < SP3 and puts every
# special above the Heavy normal attack.
_SPECIAL_DAMAGE_RATIOS = (1.75, 2.50, 3.50)


def special_damage_ratios(bid, star):
    """(s1, s2, s3) transform/special-attack damage ratios for a bot. Uniform authored
    curve for now; kept as a function so per-bot or per-class tuning can hang off it
    later the same way base_stats/max_special_attacks do."""
    return _SPECIAL_DAMAGE_RATIOS


# ---------------------------------------------------------------------------
# Defense Modules (MODS) catalog loader
# ---------------------------------------------------------------------------
def _load_mods():
    mpath = os.path.join(HERE, "mods_catalog.json")
    if os.path.exists(mpath):
        try:
            with open(mpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


# ---------------------------------------------------------------------------
# Relics catalog loader
# ---------------------------------------------------------------------------
def _load_relics():
    rpath = os.path.join(HERE, "relics_catalog.json")
    if os.path.exists(rpath):
        try:
            with open(rpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


# ---------------------------------------------------------------------------
# JSON builders -- emit the exact proven shapes from Server/responses/.
# ---------------------------------------------------------------------------
def build_blueprints(lang="en"):
    """`blueprints` map for getLoginData. Same keys as the working response:
    id, et(entity type -- 'bot' for characters, 'mod' for defense modules), s1/s2/s3
    (special-attack damage ratios), msa (max special attacks), ab (attack bonus),
    plus the gg/mfl/nfr/fcpg/fhpag fields the client reads.

    `c`/character (blueprint <Character>@0x28) links the blueprint to the characters
    map. HeroData.get_Faction (0xE8D8A0) does BCGManager.characters[blueprint.Character]
    and THROWS KeyNotFoundException if `c` is empty -> the BOTS tile's RatingWidget.SetData
    crashes with "unknown error" (verified live session 4). The characters map is keyed
    by bid, so c=bid. `r`/rarity (@0x64) and `a`/attribute_base_type (@0x70) feed the
    rarity frame + faction; both are plain field assignments (no throwing lookup)."""
    out = {}
    for bid, (faction, klass, star) in ROSTER.items():
        name = display_name(bid, lang=lang)
        s1, s2, s3 = special_damage_ratios(bid, star)
        out[bid] = {
            "id": bid, "et": "bot",
            "c": bid, "r": star, "a": faction,
            "cl": klass,
            "name": name, "name_s": name,
            "m": model_id(bid), "mdl": model_id(bid),
            "i": art_base(bid), "img": art_base(bid),
            "ma": model_id(bid), "map_asset": model_id(bid),
            "s1": s1, "s2": s2, "s3": s3,
            "msa": max_special_attacks(bid, star),
            "ab": 100.0, "gg": 1, "mfl": 0, "nfr": 0,
            "fcpg": "", "fhpag": "",
        }
    for m in _load_mods():
        mid = m["id"]
        star = m.get("default_star", 5)
        klass = m.get("class_affinity", "tech")
        mdl = m.get("model_id", mid)
        base = art_base(mid)
        name = m.get("name_zh" if lang == "zh" else "name_en", m.get("name_en", mid))
        out[mid] = {
            "id": mid, "et": "tower",
            "c": mid, "r": star, "a": "autobot",
            "cl": "",
            "name": name, "name_s": name,
            "m": mdl, "mdl": mdl,
            "i": base, "img": base,
            "ma": mdl, "map_asset": mdl,
            "s1": 1.0, "s2": 1.0, "s3": 1.0,
            "msa": 0,
            "ab": 100.0, "gg": 1, "mfl": 0, "nfr": 0,
            "fcpg": "", "fhpag": "",
        }
    for r in _load_relics():
        rid = r["id"]
        star = r.get("default_star", 5)
        mdl = r.get("model_id", rid)
        base = art_base(rid)
        name = r.get("name_zh" if lang == "zh" else "name_en", r.get("name_en", rid))
        out[rid] = {
            "id": rid, "et": "relic",
            "c": rid, "r": star, "a": "autobot",
            "cl": "",
            "name": name, "name_s": name,
            "m": mdl, "mdl": mdl,
            "i": base, "img": base,
            "ma": mdl, "map_asset": mdl,
            "s1": 1.0, "s2": 1.0, "s3": 1.0,
            "msa": 0,
            "ab": 100.0, "gg": 1, "mfl": 0, "nfr": 0,
            "fcpg": "", "fhpag": "",
        }
    return out


# Shipped portrait names are abbreviated and irregular, unlike the full mesh bundle ids.
# These values are the bases of assets/assetpack/portraits_odr/portraits/
# portrait_<base>_{large,small}; each listed base has both portrait sizes in the user's APK.
_ART_BASE = {
    # --- Scripted intro fighters ---
    "fte_optimus_gs_t3": "optimus_gs",
    "fte_stars_gs_t3": "stars_gs",

    # --- Autobots ---
    "blaster_gs_leader2016": "blastr_gs",
    "bumblebee_cin_dotm": "bumbl_c",
    "bumblebee_gs_kabam": "bumbl_gs",
    "chromia_gs_kabam": "chromia_gs",
    "cliffjumper_gs_kabam": "cliffjump_gs",
    "dinobot_bw_kabam": "dinob_bw",
    "drift_cin_aoe": "drift_c",
    "grimlock_gs_mp08": "griml_gs",
    "hotrod_cin_tlk": "hotrod_c",
    "hound_cin_tlk": "hound_c",
    "ironhide_cin_rotf": "ironh_c_rotf",
    "ironhide_gs_kabam": "ironh_gs",
    "mirage_gs_deluxe2016": "mirag_gs",
    "optimusprimal_bw_mp32": "oprimal_bw",
    "optimusprime_cin_tf": "optimus_c_tf",
    "optimusprime_sg_voyager2015": "optimus_sg",
    "ratchet_gs_kabam": "ratch_gs",
    "rhinox_gs_voyager2014": "rhino_bw",  # Only the Beast Wars-styled art ships.
    "rodimusprime_gs_mp09": "rodimus_gs",
    "sideswipe_gs": "sides_gs",
    "starsaber_gs_leader2014": "starsaber",
    "sunstreaker_gs_deluxe2008": "sunstreak_gs",
    "ultramagnus_gs_leader": "ultram_gs",
    "wheeljack_gs_mp20": "wheelj_gs",
    "windblade_gs": "windb_gs",

    # --- Decepticons ---
    "acidstorm_gs_leader2015": "acidstorm",
    "barricade_cin_dotm": "barri_c",
    "bitstream_gs_leader2015": "bitstream",
    "bludgeon_gs_rd20": "bludge_gs",
    "bonecrusher_cin_rotf": "bonec_c",
    # The misspelled clyclon_gs is large-only; use the correctly spelled paired art.
    "cyclonus_gs_uw06": "cyclon_gs",
    "deadend_gs_deluxe2015": "deadend_gs",
    "dirge_gs_deluxe2008": "dirge_gs",
    "grindor_cin_rotf": "grind_c_rotf",
    "hotlink_gs_leader2015": "hotlink",
    "ionstorm_gs_leader2015": "ionstorm",
    "kickback_gs_kabam": "kickb_gs",
    "megatron_cin_rotf": "megat_c",
    "megatron_gs_leader2015": "megat_gs",
    "megatronus_gs_kabam": "megatro_gs",
    "mixmaster_cin_rotf": "mixma_c_rotf",
    "motormaster_gs_voyager2015": "motorm_gs",
    "necrotronus_gs_kabam": "necrotro_gs",
    "nemesisprime_gs_voyager2015": "nemesis_p",
    "novastorm_gs_leader2015": "novastorm",
    "ramjet_gs_deluxe2008": "ramjet_gs",
    "shockwave_gs": "shock_c",
    "soundblaster_gs_mp13b": "soundblast_gs",
    "soundwave_gs": "sound_gs",
    "sunstorm_gs_leader2015": "sunstorm",
    "thundercracker_gs_leader2015": "thunder_gs",
    "thrust_gs_deluxe2008": "thrust",
    "waspinator_gs_deluxe": "wasp_bw",  # Only the Beast Wars-styled art ships.

    # --- Sharkticon NPC variants ---
    # The generic bot has no unnamed art, so it borrows gold. brawl is large-only;
    # the paired class portrait is the abbreviated npc_shark_braw instead.
    "sharkticon_gs_kabam": "npc_shark_gold",
    "sharkticon_gs_brawler": "npc_shark_braw",
    "sharkticon_gs_demolition": "npc_shark_demo",
    "sharkticon_gs_scout": "npc_shark_scou",
    "sharkticon_gs_tactician": "npc_shark_tact",
    "sharkticon_gs_tech": "npc_shark_tech",
    "sharkticon_gs_warrior": "npc_shark_warr",

    # --- Defense Modules (MODS) official shipped portraits ---
    "mods_primemodule_01": "primemodule",
    "mods_harmaccelerator_01": "harm",
    "mods_EMImodule_01": "emi",
    "mods_repairmodule_01": "repair",
    "mods_strangerefractor_01": "strangerefractor",
    "mods_superconductor_1000": "superconductor",
    "mods_superconductor_2000": "superconductor",
    "mods_paralyzer_01": "paralyzer",
    "mods_laserguidance_01": "laserguidance",
    "mods_nightbirdsmark_01": "nightbirdsmark",
    "mods_brawlersfury_01": "brawlersfury",
    "mods_demolitionscache_01": "democache",
    "mods_exofilter_01": "exofilter",
    "mods_fluxincapacitator_01": "flux",
    "mods_robotresource_01": "robotresource",
    "mods_scoutssentry_01": "scoutssentry",
    "mods_security_01": "security",
    "mods_tacticianstrick_02": "tacticianstrick",
    "mods_techconsole_01": "techconsole",
    "mods_warriorscall": "warriorscall",
    "mods_generic_off_01": "gen_off",
    "mods_generic_def_01": "gen_def",
    "mods_generic_utl_01": "gen_utl",
    "mods_attack_01": "attack",
    "mods_health_01": "health",

    # --- Relics official shipped portraits ---
    "relic_immobilizer": "immobilizer",
    "relic_allspark": "allspark",
    "relic_covenant_primus": "covenant_primus",
    "relic_matrix_of_leadership": "matrix_of_leadership",
    "relic_origin_matrix": "origin_matrix",
    "relic_ancienthead": "ancienthead",
    "relic_solus_forge": "solus_forge",
    "relic_dark_energon_crystal": "dark_energon_crystal",
    "relic_unstable_energon_crystal": "unstable_energon_crystal",
    "relic_stasis_generator": "stasis_generator",
    "relic_cloaking_field": "cloaking_field",
    "relic_fallen_titan_hand": "fallen_titan_hand",
    "relic_ancient_tablet": "ancient_tablet",
    "relic_goldendisk": "goldendisk",
    "relic_shattered_disk": "shattered_disk_t4",
    "relic_statue_op": "statue_op_c",
    "relic_statue_megatron": "statue_megatron",
    "relic_statue_hotrod": "statue_hotrod",
    "relic_statue_solus": "statue_solus_g",
    "relic_jazz": "relic_jazz_t4",
    "relic_optimus_primal": "relic_optimus_primal_t4",
    "relic_megatron": "relic_megatron_t4",
    "relic_bumblebee": "relic_bumblebee_t4",
    "relic_blaster": "relic_blaster_t4",
    "relic_cheetor": "relic_cheetor_t4",
    "relic_hound": "relic_hound_t4",
    "relic_galvatron": "relic_galvatron_t4",
    "relic_kickback": "relic_kickback_t4",
    "relic_alliance_victory": "relic_ave_t4",
    "relic_raid_champion": "relic_raid_t4",
}


def art_base(bid):
    """Short art base for a bot id, used for PORTRAIT asset names.

    Shipped portrait names are abbreviated and irregular. Their authoritative bases come
    from assets/assetpack/portraits_odr/portraits/portrait_<base>_{large,small}; a base
    that does not ship makes the client render the reported blank/black portrait tile.
    The two-token derivation below is only a fallback that happens to be right for 12
    roster bots, so all irregular shipped names are explicitly recorded in _ART_BASE.
    """
    if bid in _ART_BASE:
        return _ART_BASE[bid]
    parts = bid.split("_")
    return "_".join(parts[:2]) if len(parts) >= 2 else bid


# A few bots have no mesh bundle of their own and must borrow another character's mesh.
# The scripted first-time-experience (FTE) fighters are variant ids (fte_optimus_gs_t3 /
# fte_stars_gs_t3) that the game reuses for the intro Optimus-vs-Starscream duel, but the
# APK ships no fte_* asset bundle -- so their model id must point at a real mesh or the intro
# Optimus loads the generic placeholder. Optimus -> the movie Optimus Prime bundle; Starscream
# -> skywarp (the same Seeker jet mold, the closest shipped mesh; there is no Starscream bundle).
_MODEL_OVERRIDE = {
    "fte_optimus_gs_t3": "optimusprime_gs_v",
    "fte_stars_gs_t3": "starscream_gs",
}


def model_id(bid):
    """3D model / mesh asset id for a bot -- the id the client feeds to the actor loader
    to pick which character asset bundle to mount in live combat (and on the questboard).

    Unlike the 2D portrait (art_base, a SHORT name), the combat MESH bundle is named by the
    FULL bid: each character ships as `assets/assetpack/<bid>_odr/<bid>.assetbundle` with the
    ODR toc bundle key == <bid> (verified against the extracted APK, e.g.
    optimusprime_cin_tf_odr/optimusprime_cin_tf.assetbundle). CharacterWorldLoader.LoadActor
    reads BCGBlueprintBase.ModelID (_modelID@0x40, wire key m/mdl) to resolve that bundle.
    When ModelID is empty (blueprints never authored it) or truncated to the short art_base
    (optimusprime_cin), the bundle path does not exist, so EVERY fighter -- the player's
    Optimus and the Sharkticon alike -- fell back to the same generic placeholder mech
    (visible in media/mission-fight-*.mp4: both robots share one purple mesh). Returning the
    full bid makes the loader mount the character's real mesh. A few variant ids that ship
    no bundle of their own borrow a real character's mesh via _MODEL_OVERRIDE."""
    return _MODEL_OVERRIDE.get(bid, bid)


_BOT_NAMES = {
    # First-time-experience (intro duel)
    "fte_optimus_gs_t3": "Optimus Prime",
    "fte_stars_gs_t3": "Starscream",

    # Autobots
    "arcee_gs_deluxe2014": "Arcee",
    "blaster_gs_leader2016": "Blaster",
    "bumblebee_cin_dotm": "Bumblebee (DOTM)",
    "bumblebee_gs_kabam": "Bumblebee",
    "cheetor_bw_transmetal": "Cheetor",
    "cliffjumper_gs_kabam": "Cliffjumper",
    "dinobot_bw_kabam": "Dinobot",
    "drift_cin_aoe": "Drift",
    "grimlock_gs_mp08": "Grimlock",
    "hotrod_cin_tlk": "Hot Rod",
    "hound_cin_tlk": "Hound",
    "ironhide_cin_rotf": "Ironhide (ROTF)",
    "ironhide_gs_kabam": "Ironhide",
    "jazz_gs_twm05": "Jazz",
    "jetfire_gs_leader2014": "Jetfire",
    "mirage_gs_deluxe2016": "Mirage",
    "optimusprimal_bw_mp32": "Optimus Primal",
    "optimusprime_cin_tf": "Optimus Prime (MV1)",
    "optimusprime_sg_voyager2015": "SG Optimus Prime",
    "prowl_gs_deluxe2016": "Prowl",
    "ratchet_gs_kabam": "Ratchet",
    "rhinox_gs_voyager2014": "Rhinox",
    "rodimusprime_gs_mp09": "Rodimus Prime",
    "sideswipe_gs": "Sideswipe",
    "starsaber_gs_leader2014": "Star Saber",
    "sunstreaker_gs_deluxe2008": "Sunstreaker",
    "ultramagnus_gs_leader": "Ultra Magnus",
    "wheeljack_gs_mp20": "Wheeljack",
    "windblade_gs": "Windblade",

    # Decepticons
    "barricade_cin_dotm": "Barricade",
    "bludgeon_gs_rd20": "Bludgeon",
    "bonecrusher_cin_rotf": "Bonecrusher",
    "cyclonus_gs_uw06": "Cyclonus",
    "dirge_gs_deluxe2008": "Dirge",
    "galvatron_gs_voyager2016": "Galvatron",
    "grindor_cin_rotf": "Grindor",
    "kickback_gs_kabam": "Kickback",
    "megatron_cin_rotf": "Megatron (ROTF)",
    "megatron_gs_leader2015": "Megatron",
    "megatronus_gs_kabam": "Megatronus",
    "mixmaster_cin_rotf": "Mixmaster",
    "motormaster_gs_voyager2015": "Motormaster",
    "necrotronus_gs_kabam": "Necrotronus",
    "nemesisprime_gs_voyager2015": "Nemesis Prime",
    "ramjet_gs_deluxe2008": "Ramjet",
    "scorponok_bw_kabam": "Scorponok",
    "shockwave_gs": "Shockwave",
    "skywarp_gs_leader2015": "Skywarp",
    "slipstream_gs": "Slipstream",
    "soundblaster_gs_mp13b": "Soundblaster",
    "soundwave_gs": "Soundwave",
    "thundercracker_gs_leader2015": "Thundercracker",
    "tantrum_gs_kabam": "Tantrum",
    "waspinator_gs_deluxe": "Waspinator",

    # Sharkticons
    "sharkticon_gs_kabam": "Sharkticon",
    "sharkticon_gs_brawler": "Sharkticon (Brawler)",
    "sharkticon_gs_demolition": "Sharkticon (Demolition)",
    "sharkticon_gs_scout": "Sharkticon (Scout)",
    "sharkticon_gs_tactician": "Sharkticon (Tactician)",
    "sharkticon_gs_tech": "Sharkticon (Tech)",
    "sharkticon_gs_warrior": "Sharkticon (Warrior)",
}

_ZH_JSON_PATH = os.path.join(os.path.dirname(__file__), "bot_names_zh.json")
if not os.path.exists(_ZH_JSON_PATH):
    _ZH_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "bot_names_zh.json")

_BOT_NAMES_ZH = {}
if os.path.exists(_ZH_JSON_PATH):
    try:
        with open(_ZH_JSON_PATH, "r", encoding="utf-8", errors="replace") as f:
            zh_data = json.load(f)
            for k, v in zh_data.items():
                if isinstance(v, dict) and "zh" in v:
                    _BOT_NAMES_ZH[k] = v["zh"]
                elif isinstance(v, str):
                    _BOT_NAMES_ZH[k] = v
    except Exception as e:
        print(f"Warning loading {_ZH_JSON_PATH}: {e}")

_BOT_NAMES_EN = _BOT_NAMES.copy()


def display_name(bid, lang="en"):
    """Human-readable roster name for a bot id. Supports 'en' and 'zh'."""
    if lang == "zh" and bid in _BOT_NAMES_ZH:
        return _BOT_NAMES_ZH[bid]
    if bid in _BOT_NAMES_EN:
        return _BOT_NAMES_EN[bid]
    parts = bid.split("_")
    tok = parts[0]
    if tok == "fte" and len(parts) > 1:
        tok = parts[1]
    return tok[:1].upper() + tok[1:]


def build_characters(lang="en"):
    """`characters` map for getLoginData -> BCGCharacterData. Keys id, sg, gen(faction),
    aip, sps (as in the proven response) PLUS the art fields the client reads:
    i/img (_imgID@0x50), m/mdl (ModelID@0x28), ma/map_asset (MapAssetID@0x30),
    hc/hero_colour (HeroColour@0x38). These were empty, which left the roster's
    featured/valid-hero setup in HeroesScreen.SetScreenType dereferencing empty art
    (NullReferenceException -> "unknown error", verified live session 4). Assets are
    ODR-delivered so most won't actually load offline, but non-empty names keep the
    setup path from null-dereferencing."""
    out = {}
    for bid, (faction, klass, star) in ROSTER.items():
        base = art_base(bid)
        name = display_name(bid, lang=lang)
        out[bid] = {
            "id": bid,
            # FriendlyName / FriendlyNameShort (keys n_loc/n/name_loc/name and
            # ns_loc/ns/name_s_loc/name_s -- captured live). Non-null display name so
            # the roster tile's name label isn't a null string (see display_name).
            "name": name, "name_s": name,
            "sg": "", "gen": faction, "aip": "", "sps": "",
            # i/img -> portrait (SHORT art base); m/mdl -> ModelID (the 3D combat mesh
            # bundle, named by the FULL bid, see model_id). Truncating the model id to the
            # short base pointed at a non-existent bundle and forced the placeholder mesh.
            "i": base, "img": base,
            "m": model_id(bid), "mdl": model_id(bid),
            "ma": model_id(bid), "map_asset": model_id(bid),
            "hc": faction, "hero_colour": faction,
        }
    for m in _load_mods():
        mid = m["id"]
        mdl = m.get("model_id", mid)
        base = art_base(mid)
        name = m.get("name_zh" if lang == "zh" else "name_en", m.get("name_en", mid))
        out[mid] = {
            "id": mid,
            "name": name, "name_s": name,
            "sg": "", "gen": "autobot", "aip": "", "sps": "",
            "i": base, "img": base,
            "m": mdl, "mdl": mdl,
            "ma": mdl, "map_asset": mdl,
            "hc": "autobot", "hero_colour": "autobot",
        }
    for r in _load_relics():
        rid = r["id"]
        mdl = r.get("model_id", rid)
        base = art_base(rid)
        name = r.get("name_zh" if lang == "zh" else "name_en", r.get("name_en", rid))
        out[rid] = {
            "id": rid,
            "name": name, "name_s": name,
            "sg": "", "gen": "autobot", "aip": "", "sps": "",
            "i": base, "img": base,
            "m": mdl, "mdl": mdl,
            "ma": mdl, "map_asset": mdl,
            "hc": "autobot", "hero_colour": "autobot",
        }
    return out


def build_attack_values():
    """`attackValues` rows used by normal attacks in live combat.

    PlayerAttributes.GetAttackPercent converts AttackLevel through EnumMap and performs
    a case-sensitive dictionary lookup with the .NET enum names below. A missing row
    returns 0 -- there is no ``default`` fallback -- which makes hits animate without
    reducing health. Special attacks use the blueprint's s1/s2/s3 fields instead.

    BCGAttackValue parses id/a/m/c/d/p as attack id, damage percent, mana gain, critical
    chance, critical damage, and critical pierce. ``m`` feeds
    BCGAttackValue.ManaGain@0x1C, so gain per hit is ``m * HitData.Mana * power_gain``.
    TuningGameplay.ManaPerSpecial is 300 per segment, and PlayerAttributes.Init@0xDAB16C
    computes max mana as ``ManaPerSpecial * SpecialAttackCount``. All values are
    ORIGINAL authored balance for this revival, not recovered Kabam data: a 50-mana
    Light hit is about one-sixth of a segment, so roughly six landed hits enable SP1.
    """
    def av(attack_id, percent, mana_gain, crit_chance, crit_damage, crit_pierce):
        return {
            "id": attack_id,
            "a": percent,
            "m": mana_gain,
            "c": crit_chance,
            "d": crit_damage,
            "p": crit_pierce,
        }

    return {
        "Light": av("Light", 0.35, 50.0, 0.05, 1.5, 0.0),
        "Medium": av("Medium", 0.60, 75.0, 0.05, 1.5, 0.0),
        "Heavy": av("Heavy", 1.00, 120.0, 0.05, 1.5, 0.05),
        "Ranged": av("Ranged", 0.40, 55.0, 0.05, 1.5, 0.0),
    }


def build_missions_config():
    """Mission combat tuning consumed by ``TuningGameplay``.

    The client selects this config with the exact runtime mode ``bcg-combat``. A
    positive armor constant is required even while authored heroes have zero armor:
    GetArmorDR computes ``armor / (abs(armor) + constant)``, so the default 0/0
    becomes NaN and causes GetDamageReceived to clamp every hit to zero.

    ``maxQueuedActionTime`` is the authored buffered-input window in seconds. If
    omitted it defaults to zero, so queued combat actions can never execute.

    The ``user-base`` entry is the player base's CommonConfig. ActiveQuest's
    ConfigChangedCallback (@0x109F290) only builds a ``Quests.UserBaseConfig`` when a
    config named exactly ``user-base`` arrives AND the base's type is ``users``;
    without it the base ActiveQuest keeps a null config. Its two fields gate resource
    claiming from base generators.
    """
    return {
        "configsHash": "offline-v1",
        "configs": {
            "bcg-combat": {
                "armorRatingConstant": 1000.0,
                # 300.0 mirrors TuningGameplay.DeserializeData@0x1425540's built-in
                # default and documents attackValues[*].m's absolute unit; it is harmless
                # if unread, since TuningGameplay's MonoBehaviour bundle serialization
                # sets 300 per segment either way.
                "manaPerSpecial": 300.0,
                # TuningGameplay.DeserializeData@0x1425540 reads maxQueuedActionTime
                # into @0x80; QueuedAction.SetAction@0xD35130 stores TimeStamp = clock
                # + that, and HasAction@0xD351F8 returns TimeStamp > clock. This ORIGINAL
                # authored feel is the buffered-input window in seconds: leaving it unset
                # makes it 0, so queued attacks never execute.
                "maxQueuedActionTime": 0.2,
            },
            "user-base": {
                "minClaimInterval": 60,
                "minClaimPercentage": 0.1,
            },
        },
    }


def build_missions_autorefresh_result():
    """Direct ``/autorefresh/missionsconfig/refresh`` result.

    ``refresh`` is an absolute client/server time, not a delay. Zero deliberately
    keeps this manager due so grouped refreshes repeat the config after combat's
    ``TuningGameplay`` object has subscribed to config changes.
    """
    return {
        "check": "offline-v1",
        "refresh": 0,
        "cache": False,
        # Direct refresh data is keyed by manager name. Grouped updates use the
        # generic ``data`` field built below.
        "missionsconfig": build_missions_config(),
    }


def build_missions_autorefresh_update():
    """Missions-config entry in an autorefresh ``updates`` list."""
    result = build_missions_autorefresh_result()
    return {
        "name": "missionsconfig",
        "error": "",
        "check": result["check"],
        "locHash": "",
        "refresh": result["refresh"],
        "data": result["missionsconfig"],
        "cache": result["cache"],
    }


def build_missions_account_data():
    """Account bootstrap consumed by both ConfigManager and its refresh base class.

    Login passes this object directly to ``ConfigManager.OnData``, which reads the
    top-level config fields. ``AutoRefreshingManager.Connect`` later reuses the same
    object as a refresh response, so it also needs refresh metadata plus nested data
    to make missionsconfig eligible for grouped refreshes.
    """
    account_data = build_missions_config()
    account_data.update(build_missions_autorefresh_result())
    return account_data


_CLASS_NAMES = {
    "braw": "Brawler", "tact": "Tactician", "scou": "Scout",
    "demo": "Demolitions", "warr": "Warrior", "tech": "Tech",
}

# Rock-paper-scissors: each class is strong against the next in this ring and weak
# to the previous one. ORIGINAL assignment for this revival. Used to fill the
# IdealContender ("who this class beats") list in heroClasses.
_CLASS_RING = ("braw", "tact", "scou", "demo", "warr", "tech")


def build_hero_classes():
    """`heroClasses` map for getLoginData -> BCGManagerBase.HeroClassesData.
    The roster tile reads a bot's class metadata (frame/icon + attack bonus) from
    here; when this map is empty the class lookup yields nothing. Keyed by class id.
    Exact server short-codes for the inner fields are unknown, so we emit several
    aliases (the client's JSON parser ignores keys it doesn't recognise)."""
    out = {}
    for i, cid in enumerate(_CLASS_RING):
        beats = _CLASS_RING[(i + 1) % len(_CLASS_RING)]
        name = _CLASS_NAMES[cid]
        out[cid] = {
            "id": cid, "cid": cid, "class_id": cid,
            "n": name, "name": name, "class_name": name,
            "ab": 1.1, "atkb": 1.1, "attack_bonus": 1.1,
            "atkp": 0.9, "attack_penalty": 0.9,
            "ic": [beats], "ideal_contender": [beats],
        }
    return out


def build_rarity_properties():
    """`rarityProperties` map for getLoginData -> RarityPropertiesData. The roster
    tile needs the rarity (star) entry for a bot to draw its star frame; an empty
    map leaves star-N bots without a rarity definition. Keyed by star as a string."""
    out = {}
    for star in range(1, 6):
        name = f"{star} Star"
        out[str(star)] = {
            "id": str(star), "n": name, "name": name,
            "mv": star, "map_value": star,
            "sp3qt": 0.5, "sp3_quicktime": 0.5,
            "ms": 99, "max_sig": 99,
        }
    return out


# BCGHeroBase field schema, captured live (session 4) from BCGHeroBase..ctor(IDictionary)
# @ RVA 0xC21AC4 via the native hook (slot 45 ==HEROBASE== bracket -> "HB <reader> <key>"
# lines in dotkeys.log). The ctor reads exactly these keys, in this order:
#   string : id
#   int    : r m s max_hp mhpb attack attb mana_start stun_time special_attacks
#            rating rating_hp rating_attack rating_hp_base rating_attack_base ab
#   float  : hp armor crit_chance crit_damage perfect_block_chance block_proficiency
#            mana_gain resist_magic resist_physical stun_chance cr rcr rcd spb pjb cpw
#            ap bp il il2 il3 is4 eg fg ar hr hm am hrhp hra
#   list   : stat_mods sig_mods buff_mods i i2 i3 i4
# 's' is the star/rarity (drives the tile's rarity frame); the rating_* fields drive the
# RatingWidget; the rest are combat tuning that can default to 0/empty for the roster view.
def build_hero_base(bid, rank=1):
    """One BCGHeroBase record for login `heroes[bid][rank]`. Deterministic/original,
    reusing the same authored stat curve as the owned-hero + blueprint builders."""
    faction, klass, star = ROSTER.get(bid, ("decepticon", "tact", 5))
    level = max(1, rank * 10)
    hp, atk = base_stats(bid, rank, level)
    rating = (hp + atk) // 20
    return {
        "id": bid, "r": rank, "m": star, "s": star,
        "max_hp": hp, "mhpb": hp, "attack": atk, "attb": atk,
        "mana_start": _DIAG_MANA_START, "stun_time": 0,
        "special_attacks": max_special_attacks(bid, star),
        "rating": rating,
        "rating_hp": hp // 2, "rating_attack": atk // 2,
        "rating_hp_base": hp // 2, "rating_attack_base": atk // 2,
        "ab": 1,
        # combat-tuning floats: sensible neutral values (roster view doesn't need real balance)
        "hp": float(hp), "armor": 0.0, "crit_chance": 0.05, "crit_damage": 1.5,
        "perfect_block_chance": 0.1, "block_proficiency": 0.75, "mana_gain": _MANA_GAIN_RATE,
        "resist_magic": 0.0, "resist_physical": 0.0, "stun_chance": 0.05,
        "cr": 0.0, "rcr": 0.0, "rcd": 0.0, "spb": 0.0, "pjb": 0.0, "cpw": 0.0,
        "ap": 0.0, "bp": 0.0, "il": 0.0, "il2": 0.0, "il3": 0.0, "is4": 0.0,
        "eg": 0.0, "fg": 0.0, "ar": 0.0, "hr": 0.0, "hm": 0.0, "am": 0.0,
        "hrhp": 0.0, "hra": 0.0,
        "stat_mods": [], "sig_mods": [], "buff_mods": [],
        "i": [], "i2": [], "i3": [], "i4": [],
    }


def build_heroes():
    """Login-data top-level `heroes` map = BCGManager._baseHeroData (BCGHeroBaseDict:
    Dictionary<string blueprintId, Dictionary<int rank, BCGHeroBase>>). HeroData..ctor
    resolves mHeroBase from this per (blueprint,rank); mHeroBase != null => mValid =>
    the BOTS tile draws its rarity frame / rating / portrait. Provides ranks 1..5."""
    out = {}
    for bid in OWNED:
        faction, klass, star = ROSTER.get(bid, ("decepticon", "tact", 5))
        out[bid] = {str(r): build_hero_base(bid, r) for r in range(1, max(2, star + 1))}
    for m in _load_mods():
        mid = m["id"]
        star = m.get("default_star", 5)
        hp0, atk0 = _STAR_BASE.get(star, _STAR_BASE[5])
        rating = (hp0 + atk0) // 20
        out[mid] = {
            "1": {
                "id": mid, "r": 1, "m": star, "s": star,
                "max_hp": hp0, "mhpb": hp0, "attack": atk0, "attb": atk0,
                "mana_start": 0, "stun_time": 0, "special_attacks": 0,
                "rating": rating,
                "rating_hp": hp0 // 2, "rating_attack": atk0 // 2,
                "rating_hp_base": hp0 // 2, "rating_attack_base": atk0 // 2,
                "ab": 0,
                "hp": float(hp0), "armor": 500.0, "crit_chance": 0.1, "crit_damage": 1.5,
                "perfect_block_chance": 0.1, "block_proficiency": 0.75, "mana_gain": 1.0,
                "resist_magic": 0.0, "resist_physical": 0.0, "stun_chance": 0.0,
                "cr": 0.0, "rcr": 0.0, "rcd": 0.0, "spb": 0.0, "pjb": 0.0, "cpw": 0.0,
                "ap": 0.0, "bp": 0.0, "il": 0.0, "il2": 0.0, "il3": 0.0, "is4": 0.0,
                "eg": 0.0, "fg": 0.0, "ar": 0.0, "hr": 0.0, "hm": 0.0, "am": 0.0,
                "hrhp": 0.0, "hra": 0.0,
                "stat_mods": [], "sig_mods": [], "buff_mods": [],
                "i": [], "i2": [], "i3": [], "i4": [],
            }
        }
    for r in _load_relics():
        rid = r["id"]
        star = r.get("default_star", 5)
        hp0, atk0 = _STAR_BASE.get(star, _STAR_BASE[5])
        rating = (hp0 + atk0) // 20
        out[rid] = {
            "1": {
                "id": rid, "r": 1, "m": star, "s": star,
                "max_hp": hp0, "mhpb": hp0, "attack": atk0, "attb": atk0,
                "mana_start": 0, "stun_time": 0, "special_attacks": 0,
                "rating": rating,
                "rating_hp": hp0 // 2, "rating_attack": atk0 // 2,
                "rating_hp_base": hp0 // 2, "rating_attack_base": atk0 // 2,
                "ab": 0,
                "hp": float(hp0), "armor": 500.0, "crit_chance": 0.1, "crit_damage": 1.5,
                "perfect_block_chance": 0.1, "block_proficiency": 0.75, "mana_gain": 1.0,
                "resist_magic": 0.0, "resist_physical": 0.0, "stun_chance": 0.0,
                "cr": 0.0, "rcr": 0.0, "rcd": 0.0, "spb": 0.0, "pjb": 0.0, "cpw": 0.0,
                "ap": 0.0, "bp": 0.0, "il": 0.0, "il2": 0.0, "il3": 0.0, "is4": 0.0,
                "eg": 0.0, "fg": 0.0, "ar": 0.0, "hr": 0.0, "hm": 0.0, "am": 0.0,
                "hrhp": 0.0, "hra": 0.0,
                "stat_mods": [], "sig_mods": [], "buff_mods": [],
                "i": [], "i2": [], "i3": [], "i4": [],
            }
        }
    return out


def build_stat_modifiers():
    """Original offline stat modifiers keyed exactly as BCGStatModifierDict expects.

    The complete short-key schema was captured live in seg-03.  `gp_hit_stun` is
    registered by PlayerController.DefaultStatMods, so it intentionally needs no
    per-hero stat_mods/buff_mods reference.
    """
    return {
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
            # ApplyHitStun supplies the gameplay duration.  This is only a
            # 0.5-second authored fallback, intentionally in the observed window.
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
    }


def build_login_data(lang="en"):
    """Full getLoginData result. Preserves every top-level key from the proven
    response and only enriches blueprints / characters / attackValues plus the
    previously-empty heroClasses / rarityProperties tuning maps."""
    return {
        "cdn": CDN,
        "sigLvlMax": 99,
        "ratingPrecision": 4,
        "heroRatingAttackWeight": 1.0,
        "heroRatingMaxHPWeight": 1.0,
        "attributeGrowthDefs": [],
        "statMods": build_stat_modifiers(),
        "statModAppears": {},
        # NOTE (session 3): this map is BCGManager._baseHeroData (BCGHeroBaseDict), the per-
        # (blueprint,rank) BASE-ATTRIBUTE templates -> structure heroes[blueprintId][rank] =
        # { <BCGHeroBase fields, parsed by BCGHeroBase..ctor RVA 0xC21AC4> }. It is EMPTY here,
        # which is THE reason the BOTS roster renders no tiles: HeroData..ctor can't resolve
        # mHeroBase -> mValid stays false -> the tile's rarity frame / rating / portrait path all
        # fail (see tftf-offline-status memory, session 3). Authoring this (with the real key
        # shape + per-rank stats) is the fix. Left {} until the exact BCGHeroBase JSON is captured.
        "heroes": build_heroes(),
        "blueprints": build_blueprints(lang=lang),
        "evoBlueprints": {},
        "characters": build_characters(lang=lang),
        "synergyBonuses": {},
        "attackValues": build_attack_values(),
        "blueprintBonuses": {},
        "heroClasses": build_hero_classes(),
        "staminaRegen": {},
        "rarityProperties": build_rarity_properties(),
        "evoCosts": {},
        "curves": {},
    }


def build_hero_entry(bid, rank=None, level=None):
    """One owned-hero record for getUserData `updates.heroes`. Same keys as the
    proven single-hero response; entity_type MUST be 'bot'.
    Defaults to full 5-Star Rank 5 Level 50 Awakened (sig_lvl 100, flvl 100)."""
    faction, klass, star = ROSTER.get(bid, ("decepticon", "tact", 5))
    if rank is None:
        rank = max(1, star)
    if level is None:
        level = rank * 10
    hp, atk = base_stats(bid, rank, level)
    return {
        "entity_type": "bot", "bid": bid,
        "rank": rank, "level": level, "sig_lvl": 100,
        "required_xp": 0, "max_xp": 100,
        "stamina": 100, "stamina_ts": 0, "stamina_full_ts": 0, "stt": "",
        "max_hp": hp, "attack": atk,
        "rating": (hp + atk) // 20,
        "rating_attack": atk // 2, "rating_hp": hp // 2,
        "rating_attack_base": atk // 2, "rating_hp_base": hp // 2,
        "special_attacks": max_special_attacks(bid, star), "pvpb": {}, "exc": {},
        "mana_gain": _MANA_GAIN_RATE, "mana_start": _DIAG_MANA_START,
        "flvl": 100, "req_fxp": 0, "max_fxp": 100, "mfl": 100,
    }


# Default squad expanded to 5 members
DEFAULT_TEAM = [
    "optimusprime_cin_tf",
    "optimusprimal_bw_mp32",
    "megatron_gs_leader2015",
    "megatronus_gs_kabam",
    "necrotronus_gs_kabam",
]

# 6 distinct sentinels for the 6 enemy nodes (all distinct from DEFAULT_TEAM)
ENCOUNTER_SENTINELS = [
    "barricade_cin_dotm",
    "bonecrusher_cin_rotf",
    "drift_cin_aoe",
    "hound_cin_tlk",
    "ironhide_cin_rotf",
    "galvatron_gs_voyager2016",  # Final boss sentinel
]

# STORY 1.1.1 7x7 board with 6 enemy encounters (5 patrols + 1 final boss)
QUEST_DIM = 7
QUEST_PATH_COL = 1
# row on the walkable column -> (entity/blueprint key, is_final_boss, tile label)
QUEST_ENCOUNTERS = {
    1: (ENCOUNTER_SENTINELS[0], False, "Encounter 1"),
    2: (ENCOUNTER_SENTINELS[1], False, "Encounter 2"),
    3: (ENCOUNTER_SENTINELS[2], False, "Encounter 3"),
    4: (ENCOUNTER_SENTINELS[3], False, "Encounter 4"),
    5: (ENCOUNTER_SENTINELS[4], False, "Encounter 5"),
    6: (ENCOUNTER_SENTINELS[5], True, "Boss"),
}


# Live verification showed that changing only quest-begin updates its progression while the
# board marker and prefight selector retain the active-team data folded from user-data updates.
# Keep every team-producing response on one validated squad: an unknown bid otherwise becomes
# an unresolvable hero there and leaves the board marker blank.
def resolve_team(team=None):
    """Normalize an optional client squad, preserving DEFAULT_TEAM as the safe fallback."""
    try:
        bids = list(team) if team else list(DEFAULT_TEAM)
    except TypeError:
        bids = list(DEFAULT_TEAM)
    if not bids or any(not isinstance(bid, str) or bid not in ROSTER for bid in bids):
        return list(DEFAULT_TEAM)
    return bids

# --- Story-fight ARENA -------------------------------------------------------
# QuestBoss `mapOverride`@0x88 and `todIndex`@0x90 select the 3D fight arena. The
# client carries them through QuestBoss -> Quests.OnFight(sceneName, timeOfDay) ->
# FightFlow.sceneName@0x40 / FightFlow.timeOfDay@0x48 ->
# FightData.SceneName@0x20 / FightData.TimeOfDay@0x14 ->
# BattleArbiter.SceneName@0xA8 / BattleArbiter.TimeOfDayName@0xB8. The final
# time-of-day prefab name is `<level>_timeofday_<idx>_<lightmaptype>`, assembled by
# EBTimeOfDayManager.GetMergedTimeOfDayName (dump.cs:374351).
#
# An empty mapOverride means no arena is assigned, so the client falls back to karnak. Live
# verification showed that karnak's ground terrain renders black in this offline build, so it
# must remain selectable but cannot be the default. chicago was verified live to render its
# ground and street completely, which is why it is the default below. TFTF_ARENA_LEVEL and
# TFTF_ARENA_TOD make on-device sweeps of the other shipped levels cheap. This inventory was
# measured from the shipped per-pack toc.txt files. primordial, ruinedcity, and aoe are
# deliberately excluded because none ships its `<name>_merged` geometry prefab. These names
# are only asset IDs already inside the user's APK: no game asset is vendored, copied, or
# committed here (see COMPLIANCE.md's copyright-compliance rule).
ARENA_LEVELS = {
    "chicago":  (0, 1, 2),
    "hongkong": (0, 1, 2),
    "karnak":   (0, 1, 2),
    "mine":     (0, 1, 2),
    "rust":     (0, 1, 2),
}

ARENA_LEVEL = os.environ.get("TFTF_ARENA_LEVEL", "chicago")
ARENA_TOD_INDEX = int(os.environ.get("TFTF_ARENA_TOD", "0"))

if ARENA_LEVEL not in ARENA_LEVELS:
    raise ValueError(
        "Invalid TFTF_ARENA_LEVEL %r; valid levels: %s"
        % (ARENA_LEVEL, ", ".join(ARENA_LEVELS))
    )
if ARENA_TOD_INDEX not in ARENA_LEVELS[ARENA_LEVEL]:
    raise ValueError(
        "Invalid TFTF_ARENA_TOD %r for level %r; valid indices: %s"
        % (ARENA_TOD_INDEX, ARENA_LEVEL, ARENA_LEVELS[ARENA_LEVEL])
    )


def build_saved_team(team_id="0", heroes=None):
    bids = resolve_team(heroes)
    hero_dicts = [build_hero_entry(b) for b in bids]
    return {
        "sid": team_id,
        "heroes": hero_dicts,
    }


# A BCGUserActiveTeam for the getUserData `updates.activeTeams` array. QuestFlow.CalculateFlowState
# gates the STORY quest-begin -> mission-board transition on GetActiveTeam(id) @0xC1FFDC returning
# non-null; id is the ActiveQuest's team id, format "<qid>-<teamID>" (e.g. "1.1.1-0"). That looks up
# BCGUserData.activeTeams (BCGUserActiveTeamDict @0x30), keyed by BCGUserActiveTeam.ActivityID (@0x10,
# the first Dot.String the ctor @0xA610F0 reads; confirmed as the dict fold-key in
# BCGManagerBase.HandleUserDataUpdates @0x1696F14). With an empty activeTeams the lookup returned null
# and CalculateFlowState stayed at BeginQuest(1) forever (the ~14/sec quest-begin retry loop / blank
# board). Providing this entry advanced the flow all the way to LoadGameBoard (state 4). The wire
# key names below were confirmed live via the ==ATCTOR== ctor bracket + FDS2 Dot.String log:
#   aid -> ActivityID (the dict key; must equal "<qid>-<teamID>"), type -> Type, modes -> Modes,
#   expire -> EstimatedExpire, heroes -> TeamHeroes. Unlike BCGUserSavedTeam, the active-team
# ctor reads `heroes` with Dot.Object and enumerates the dictionary values before constructing
# each BCGHeroDetails. Sending an array makes Dot.Object fall back to an empty dictionary, which
# leaves TeamData with no lead character and prevents QuestPlayerController from loading an actor.
def build_active_team(activity_id="1.1.1-0", heroes=None):
    bids = resolve_team(heroes)
    hero_dicts = {b: build_hero_entry(b) for b in bids}
    return {
        "aid": activity_id,
        "type": "PvE", "modes": ["PvE"],
        "heroes": hero_dicts, "expire": 0,
    }


def build_mod_entry(mid, rank=1, level=1):
    """One owned-module record for getUserData `updates.heroes` (entity_type='tower')."""
    mod_dict = {m["id"]: m for m in _load_mods()}
    mod_info = mod_dict.get(mid, {})
    star = mod_info.get("default_star", 5)
    hp0, atk0 = _STAR_BASE.get(star, _STAR_BASE[5])
    rating = (hp0 + atk0) // 20
    return {
        "entity_type": "tower", "bid": mid,
        "rank": rank, "level": level, "sig_lvl": 0,
        "required_xp": 0, "max_xp": 100,
        "stamina": 100, "stamina_ts": 0, "stamina_full_ts": 0, "stt": "",
        "max_hp": hp0, "attack": atk0,
        "rating": rating,
        "rating_attack": atk0 // 2, "rating_hp": hp0 // 2,
        "rating_attack_base": atk0 // 2, "rating_hp_base": hp0 // 2,
        "special_attacks": 0, "pvpb": {}, "exc": {},
        "mana_gain": 1.0, "mana_start": 0,
        "flvl": 0, "req_fxp": 0, "max_fxp": 0, "mfl": 0,
    }


def build_relic_entry(rid, rank=1, level=1):
    """One owned-relic record for getUserData `updates.heroes` (entity_type='relic')."""
    relic_dict = {r["id"]: r for r in _load_relics()}
    relic_info = relic_dict.get(rid, {})
    star = relic_info.get("default_star", 5)
    hp0, atk0 = _STAR_BASE.get(star, _STAR_BASE[5])
    rating = (hp0 + atk0) // 20
    return {
        "entity_type": "relic", "bid": rid,
        "rank": rank, "level": level, "sig_lvl": 0,
        "required_xp": 0, "max_xp": 100,
        "stamina": 100, "stamina_ts": 0, "stamina_full_ts": 0, "stt": "",
        "max_hp": hp0, "attack": atk0,
        "rating": rating,
        "rating_attack": atk0 // 2, "rating_hp": hp0 // 2,
        "rating_attack_base": atk0 // 2, "rating_hp_base": hp0 // 2,
        "special_attacks": 0, "pvpb": {}, "exc": {},
        "mana_gain": 1.0, "mana_start": 0,
        "flvl": 0, "req_fxp": 0, "max_fxp": 0, "mfl": 0,
    }


def build_user_data(team=None):
    """Full getUserData result. userData maxes + owned heroes through `updates`,
    exactly as the proven response and the README/TECHNICAL_NOTES describe."""
    heroes = [build_hero_entry(bid) for bid in OWNED]
    mods = [build_mod_entry(m["id"]) for m in _load_mods()]
    relics = [build_relic_entry(r["id"]) for r in _load_relics()]
    return {
        # teamSizeMax expanded to 5 as requested
        "userData": {"blueprintsMax": 500, "teamSizeMax": 5, "teamCountMax": 5, "BotDupedTut": {"id": "BotDupedTut", "state": 2, "completed": True, "branch": ""}, "BotDupedTutorial": {"id": "BotDupedTutorial", "state": 2, "completed": True, "branch": ""}, "ForgeBotTut": {"id": "ForgeBotTut", "state": 2, "completed": True, "branch": ""}, "ForgeBotTutorial": {"id": "ForgeBotTutorial", "state": 2, "completed": True, "branch": ""}, "ForgeModTut": {"id": "ForgeModTut", "state": 2, "completed": True, "branch": ""}, "ForgeModTutorial": {"id": "ForgeModTutorial", "state": 2, "completed": True, "branch": ""}, "RankUpTut": {"id": "RankUpTut", "state": 2, "completed": True, "branch": ""}, "RankUpTutorial": {"id": "RankUpTutorial", "state": 2, "completed": True, "branch": ""}, "UpgradeBotsScreen": {"id": "UpgradeBotsScreen", "state": 2, "completed": True, "branch": ""}, "RelicTut": {"id": "RelicTut", "state": 2, "completed": True, "branch": ""}, "RelicsTutorial": {"id": "RelicsTutorial", "state": 2, "completed": True, "branch": ""}, "MasteryPointIntro": {"id": "MasteryPointIntro", "state": 2, "completed": True, "branch": ""}, "MasteriesTutorial": {"id": "MasteriesTutorial", "state": 2, "completed": True, "branch": ""}, "MasteryPointTutorial": {"id": "MasteryPointTutorial", "state": 2, "completed": True, "branch": ""}, "ShieldTutorial": {"id": "ShieldTutorial", "state": 2, "completed": True, "branch": ""}, "AutoFightTutorial": {"id": "AutoFightTutorial", "state": 2, "completed": True, "branch": ""}, "AvoidanceTutorial": {"id": "AvoidanceTutorial", "state": 2, "completed": True, "branch": ""}, "ClassAdvantageTutorial": {"id": "ClassAdvantageTutorial", "state": 2, "completed": True, "branch": ""}, "ClassGateTutorial": {"id": "ClassGateTutorial", "state": 2, "completed": True, "branch": ""}, "LinkNodesTutorial": {"id": "LinkNodesTutorial", "state": 2, "completed": True, "branch": ""}, "RaidsTutorial": {"id": "RaidsTutorial", "state": 2, "completed": True, "branch": ""}, "RaidTutorial": {"id": "RaidTutorial", "state": 2, "completed": True, "branch": ""}, "StashTutorial": {"id": "StashTutorial", "state": 2, "completed": True, "branch": ""}, "TreasuryTutorial": {"id": "TreasuryTutorial", "state": 2, "completed": True, "branch": ""}, "SparksTutorial": {"id": "SparksTutorial", "state": 2, "completed": True, "branch": ""}, "ArenaTutorial": {"id": "ArenaTutorial", "state": 2, "completed": True, "branch": ""}, "AllianceEventsTutorial": {"id": "AllianceEventsTutorial", "state": 2, "completed": True, "branch": ""}, "DailyMissionsTutorial": {"id": "DailyMissionsTutorial", "state": 2, "completed": True, "branch": ""}, "BotPlacementTutorial": {"id": "BotPlacementTutorial", "state": 2, "completed": True, "branch": ""}},
        "updates": {"heroes": heroes + mods + relics, "savedTeams": [build_saved_team(heroes=team)],
                    "activeTeams": [build_active_team(heroes=team)]},
        "deletes": {},
    }


def build_quest_summary(mission_id="1.1.1", set_id="story_act1"):
    """The detailed mission Summary (result["data"] of quest-detail; also ActiveQuest.data
    in quest-begin). Fields mirror the quest-list availableQuests entry plus detail-only
    battle/map data, discovered empirically from the client's FDS2 field-name log."""
    parts = mission_id.split(".")
    act = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 1
    chapter = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    mission = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
    return {
        "id": mission_id, "setId": set_id, "hash": "h1",
        "act": act, "chapter": chapter, "mission": mission,
        "missionIndex": mission, "index": mission,
        "friendlyName": "Arrival", "description": "The first battle.",
        "category": "story", "difficulty": "normal",
        "energyPerTile": 1, "minXpPerTile": 1, "maxXpPerTile": 2,
        "minHealthPerTile": 100, "maxHealthPerTile": 100,
        "image": "", "theme": "primordial", "todIndex": 0,
    }


def build_quest_detail(mission_id="1.1.1", set_id="story_act1"):
    """POST /quests/quest-detail/<mission_id> reply. QuestDB.AddQuestDetails (0x12E4110)
    reads result["data"] as the detailed mission Summary (via Summary.Deserialize, the
    FDS2 reader), then Legacy.QuestSet.AddQuestDetails (0x103A0E4) reads result["progression"]
    and a second maps object (literal @0x2c2b590, key name being confirmed live). Empty
    progression/maps for now -- the structure is being discovered empirically."""
    return {
        "data": build_quest_summary(mission_id, set_id),
        "progression": {},
    }


def build_quest_map(qid="1.1.1"):
    """The QuestMap object (ActiveQuest.map). Disassembly of base Map.Deserialize
    (@0x14837EC) shows the wire shape precisely:
      - `mapHash`(String), `gridDimension`(Integer): the grid is allocated as a SQUARE
        MapTile[gridDimension, gridDimension] 2D array.
      - `grid`(Array): a NESTED array -- exactly gridDimension rows, each row an array of
        exactly gridDimension tile dicts (the loop indexes outer[0..dim-1] then
        inner[0..dim-1]; every cell must be a non-null dict or the parse errors). The tile's
        position is taken from the (row, col) loop indices, NOT from any wire key. Each cell
        is deserialized by QuestMapTile.Deserialize -> base MapTile.Deserialize; base
        Serializable.Deserialize returns true unconditionally, so even `{}` is a valid tile.
      - `walkableCount`/`visibleWalkableCount`(Integer), `pathData`(Array), `overrideZoom`(f).
    MapTile wire keys (all optional, from MapTileJSONKeys @309090): `start`/`final`/`hidden`/
    `walkable`(bool), `barrier`/`item`/`dialogue`/`dialoguePE`(string). start=true -> startTile,
    final=true -> endTile. QuestMapTile adds label/timeLimit/boss/etc (LegacyDeserialize)."""
    dim = QUEST_DIM

    def tile(**kw):
        t = {"walkable": True, "hidden": False}
        t.update(kw)
        return t

    # 3x3 grid, indexed grid[row][col]. Straight walkable path down the middle column
    # (col=1): start at (0,1), an encounter at (1,1), and boss/final at (2,1). Edge columns
    # are non-walkable filler. The path now carries an encounter on the intermediate node as
    # well as the final tile.
    # Tile wire keys (harvested live from QuestMapTile.Deserialize via the FDS2/dA field log):
    # base MapTile has start/final/hidden/walkable(bool); QuestMapTile adds `lab`/`lab_loc`
    # (label), `boss`(BCGEntity)/`bossSlot`, `bt`/`db`/`pt`(arrays), `renderTemplate`, `bg`,
    # `timeLimit`. `label`/`nodeNumber` (used before) are NOT real keys and were ignored -- the
    # node label comes from `lab`. The final tile carries the first authored BCG encounter.
    # `entities` is a DICTIONARY keyed by the entity's stable id. MapTile.Deserialize reads
    # each value's `entityType` and `parentEntityType`, asks Quests.Builder.NewEntity for the
    # concrete instance, then calls Entity/QuestBoss/BCGEntity.Deserialize on that same value.
    # `boss` is the key of that entity and is how QuestMapTile links its encounter controller.
    # A tile's `links` are the ABSOLUTE positions it can be moved to (its walkable neighbours).
    # This is what makes movement possible at all: Gameboard.RequestMove(Direction) (@0xA54540)
    # gates every move on Gameboard.IsMoveValid (@0xA547E4), which ends in
    #     currentTile.links.Contains(player.position + GetOffsetFromDirection(dir))
    # (links is MapTile @0x58; the tail call at 0xA548B4 is the List<Vector2>.Contains). With no
    # links the Contains is always false, so RequestMove returns before ever posting a move --
    # which is why the board sat inert (no node response, no client traffic at all).
    # `links` is NOT in MapTileJSONKeys; MapTile.Deserialize reads it late (+0xf3c) through
    # Tools.GetVector2List (@0x1242828) using a metadata-indexed literal. Harvested live with a
    # temp hook on GetVector2List: the keys are exactly `links`, `visibleLinks` and `bt`
    # (buffTargets), and every tile we authored was logged as `links count=0`.
    # `visibleLinks` mirrors links (it drives the drawn path segments between nodes).
    # Direction offsets (float tables @0x22754e0/@0x2275500, dir order N,S,E,W,NW,NE,SW,SE) are
    # N=(0,-1) S=(0,+1) E=(+1,0) W=(-1,0) -- x is the GetTile row, y the column. Our path runs
    # down the middle column (y=1) varying the row, so a step along it is EAST/WEST.
    def links_for(row, col):
        if col != 1:
            return []
        return [{"x": r, "y": 1} for r in (row - 1, row + 1) if 0 <= r < dim]

    grid = []
    for row in range(dim):
        r = []
        for col in range(dim):
            if col == QUEST_PATH_COL:
                lk = links_for(row, col)
                if row == 0:
                    r.append(tile(start=True, lab="Start", links=lk, visibleLinks=lk))
                elif row in QUEST_ENCOUNTERS:
                    key, is_final_boss, label = QUEST_ENCOUNTERS[row]
                    r.append(tile(
                        final=(row == dim - 1), lab=label, links=lk, visibleLinks=lk,
                        boss=key,
                        entities={
                            key: build_quest_enemy(key=key, is_final_boss=is_final_boss),
                        },
                    ))
                else:
                    r.append(tile(lab="Node %d" % row, links=lk, visibleLinks=lk))
            else:
                r.append(tile(walkable=False, hidden=True))
        grid.append(r)

    # pathData drives Quests.Map.paths (@0x50). Map.Deserialize (@0x14837EC) reads pathData
    # via EB.Dot.Array; if its element count < 1 it stores paths = NULL (str xzr,[map,#0x50]
    # @0x1484084) -- which makes Quests.Presentation.PathAnalyzer.GetPathsFromMap (@0xB3C718)
    # NRE on the `ldr x0,[map,#0x50]; cbz x0` null-check at board build (Gameboard.DoSetup).
    # So pathData MUST have >=1 element. Each element becomes a MapPath via
    # MapPath..ctor(map, dict) (@0x14840FC), which reads a Vector2-list wire key through
    # GetVector2List (@0x1242828 -> EB.Dot.Array with a NON-null empty-array default). A
    # missing/unknown key therefore yields an EMPTY (not null) tiles list -- safe: Path..ctor
    # (@0xD2A704) `cbz tiles` short-circuits, so an empty MapPath renders without a crash.
    # One empty path element makes paths non-null but yields a 0-tile MapPath, which
    # leaves the board with no nodes and the DoSetup coroutine stalls on LOADING. A real
    # path is needed: each pathData element is a MapPath dict with a `path` key (confirmed
    # live: MapPath..ctor -> GetVector2List reads EB.Dot.Array("path")). `path` is a list of
    # Vector2 elements, each a dict of two INTEGER keys -> (x, y) (GetVector2List reads them
    # via EB.Dot.Integer). map.GetTile(x, y) (@0x14849c8) indexes grid[x, y] with x=row,
    # y=col (index = x*dim + y). Our walkable path is the middle column (col=1), rows 0..2.
    # x/y sub-key names are being confirmed live this drive; author the straight column path.
    path_data = [{
        "path": [{"x": r, "y": 1} for r in range(dim)],
    }]

    return {
        "hash": "qm_%s" % qid, "v": 1, "mapHash": "qm_%s" % qid,
        "gridDimension": dim,
        "grid": grid,
        "walkableCount": dim,           # 3 walkable tiles in the middle column
        "visibleWalkableCount": dim,
        "pathData": path_data,
        "overrideZoom": 0,
    }


def build_quest_enemy(map_override=None, tod_index=None, key=None, is_final_boss=True):
    """An authored STORY BCGEntity in the exact QuestBoss wire schema.

    The field names were captured from the live QuestBoss.Deserialize call after the first
    entity successfully selected Quests.BCGEntity in Builder.NewEntity. In particular the
    compact keys are `characters`, `sig_lvl`, `flvl`, `aiString`, and `aiPer`; the earlier
    property-name guesses were silently ignored and produced the anonymous 8888 placeholder.
    The entity key doubles as the combat blueprint id sent to /bcg/getBaseHeroData; non-final
    encounters set isFinalBoss=False, while only the last path tile is the final boss.
    """
    map_override = ARENA_LEVEL if map_override is None else map_override
    tod_index = ARENA_TOD_INDEX if tod_index is None else tod_index
    key = (ENCOUNTER_SENTINELS[-1] if is_final_boss else ENCOUNTER_SENTINELS[0]) if key is None else key
    return {
        # The entity key doubles as the combat blueprint id. PrefightScreenData sends it
        # verbatim to /bcg/getBaseHeroData; an arbitrary encounter id therefore creates a
        # real BCGEntity but an invalid/anonymous combatant.
        "key": key,
        "entityType": "boss",
        "parentEntityType": "boss",
        "isFinalBoss": is_final_boss,
        "characters": [key],
        "rank": 1, "level": 1, "sig_lvl": 0, "flvl": 0,
        "aiType": 0, "aiString": "default", "aiPer": "default",
        "mapOverride": map_override, "todIndex": tod_index,
    }


LOCAL_UID = "1000000000001"   # POST /auth/login result.user.uid (get_LocalUserId)


def build_quest_progression(qid="1.1.1", start=(0, 1), team=None):
    """The per-instance QuestProgression data (the instance dict IS the data passed to
    QuestProgression..ctor @0xCA5684). This is what puts the PLAYER (and thus the camera focus)
    on the board so the tappable nodes become visible/reachable.

    Disassembly of QuestProgression..ctor + Gameboard.SetPlayerPosition/InitializePlayer:
      - The board's local player = ActiveQuest.get_player() (@0x10A02CC) = quest.mission(the
        QuestProgression).localPlayer(@0x80). SetPlayerPosition (@0xA52804) BAILS if get_player()
        is null -> no player, no camera focus, invisible nodes.
      - QuestProgression..ctor iterates the `users` dict (key = uid string). For the entry whose
        key == get_LocalUserId() (@0x146C1B0 -> our POST/auth/login uid 1000000000001) it builds a
        Player via Player..ctor(Id, thisProgression, data) (@0xDAA80C) and stores it as
        localPlayer(@0x80). Every other key becomes a remote entry in users(@0x88). So `users` MUST
        contain a "1000000000001" entry for the local player to exist.
      - The local player's position = Player.get_position (@0xDAA948) = progression.currentPos(@0x18)
        (it reads the PROGRESSION's currentPos, not the user's), so `currentPos` here places the
        player on a tile. GetTile uses (x=row, y=col); our walkable path is the middle column
        (col=1), so start (row=0, col=1) is the entry tile.
    The user value dict fields (harvested QS vocab: name/tag/strongestHero/team/currentPos/points).
    `team` is read with Dot.Object and folded into List<QuestUserHero>; its dictionary keys are
    blueprint ids and each value supplies the quest-local health/rating record. It is not the
    BCGUserActiveTeam `heroes` dictionary: the pre-fight provider builds its selectable HeroData
    from this local QuestUserInfo team."""
    sx, sy = start
    bids = resolve_team(team)
    quest_team = {}
    # This quest-local dictionary is what the pre-fight bot selector enumerates.
    # Truncating it silently drops chosen squad members from the mission.
    for bid in bids:
        faction, klass, star = ROSTER.get(bid, ("decepticon", "tact", 5))
        rank = max(1, star)
        level = rank * 10
        hp, atk = base_stats(bid, rank, level)
        quest_team[bid] = {
            "hp": 1.0,
            "pi": (hp + atk) // 20,
            "sig_lvl": 100,
            "stat_mods": [],
            "sig_mods": [],
        }
    user = {
        "name": "Commander", "tag": "", "strongestHero": bids[0],
        "currentPos": {"x": sx, "y": sy},
        "team": quest_team, "points": 0,
    }
    return {
        "version": 1,
        "currentPos": {"x": sx, "y": sy},
        "cleared": [],
        "previouslyCleared": [],
        # revealed = List<QuestTileProgressionNode>; each authored as a tile position so the path
        # tiles read as revealed (non-hidden path tiles are visible regardless, but keep it explicit).
        "revealed": [{"x": r, "y": 1} for r in range(3)],
        # users keyed by uid string; the local-uid entry becomes the board player (see above).
        "users": {LOCAL_UID: user},
    }


def build_active_quest(qid="1.1.1", set_id="story_act1", team=None):
    """The per-qid VALUE object in quest-begin's result["activeQuests"] dict. Disassembly of
    QuestDB.DeserializeActiveQuests (@0x12E43EC) shows: activeQuests is a Dictionary keyed by
    qid; each value is enumerated, an inner ARRAY is read via Dot.Array (the per-quest instance
    list), and ActiveQuest.ctor(idStr, thisValueDict, instanceElement, index, bgs) is called
    ONCE PER array element (@0x12E47C8). So this object must carry (a) a non-empty instance array
    under the Dot.Array key, plus (b) the quest fields ActiveQuest.ctor reads (data/map/category).
    The Dot.Array key is being harvested live (hook slot 78); until confirmed, emit the array under
    several candidate keys so at least one matches and BuildActiveQuest fires -> ctor keys log."""
    qmap = build_quest_map(qid)
    instance = {
        "id": qid, "qid": qid, "index": 0, "instanceIndex": 0,
        "phase": 0, "startTime": 0, "expiryTime": 0,
        "data": build_quest_summary(qid, set_id),
        "map": qmap,
    }
    # ActiveQuest..ctor (@0xC38BC8) builds the QuestProgression from
    #   Dot.Object(<key>, instance)   (@0xC38FF4 -> stored to sp+0x50 -> QuestProgression..ctor x2)
    # -- an instance-only read (no quest-level fallback, unlike the `data`/`map` reads just above
    # it). So the progression wire data is a NESTED object on the instance, not flat instance keys:
    # with it absent the ctor got data==null and every field fell back to its default, which is why
    # currentPos read back as (0,0) live even though `QS O currentPos` appeared in the key log
    # (Dot.Object still logs the key when obj is null). Keep the flat copy too -- harmless, and it
    # is what the session-17 board-render milestone shipped with.
    progression = build_quest_progression(qid, team=team)
    instance["progression"] = progression
    instance.update(progression)
    arr = [instance]
    return {
        "uniqueId": qid, "qid": qid, "id": qid,
        # category is matched as a STRING by QuestDB.GetActiveQuest (op_Inequality);
        # the active-quest taxonomy the client queries is PvE/AvE/AvA (a story mission is
        # PvE), NOT the set-visibility category "Story". A "story" here made
        # GetActiveQuest("PvE") return null, so QuestFlow.CalculateFlowState never advanced
        # past BeginQuest and the client re-POSTed quest-begin forever.
        "category": "PvE", "mode": "PvE",
        "setId": set_id, "hash": "h1", "phase": 0,
        "data": build_quest_summary(qid, set_id),
        "map": qmap,
        "progression": {},
        # `instances` is the confirmed Dot.Array key iterated by DeserializeActiveQuests.
        "instances": arr,
    }


def build_quest_begin(qid="1.1.1", set_id="story_act1", team=None):
    """POST /quests/quest-begin/<qid> reply. QuestDB.DeserializeActiveQuests reads
    result["activeQuests"] via Dot.Object -> it must be a DICTIONARY keyed by qid (an array
    yields null and the parse exits immediately, which is what left combat unloaded). Each value
    is a per-quest object (see build_active_quest)."""
    return {
        "activeQuests": {qid: build_active_quest(qid, set_id, team)},
    }


def build_quest_movedir(qid="1.1.1", offx=1, offy=0, start=(0, 1), team=None):
    """POST /quests/quest-movedir/<qid>-<teamId>/<offX>/<offY> reply. This is what makes the
    player VISIBLY move one tile on the board.

    RESPONSE FLOW (disassembled this session):
      QuestsAPI move callback -> QuestsManager.<>c__DisplayClass69_0.b__0(error, data) @0xCDD92C:
        if String.IsNullOrEmpty(error) and displayClass.quest != null:
          QuestsManager.ProcessActionResultsAndProgression(quest, data) @0xD65D88, which:
            - ActiveQuest.AddActionResultsAndUpdateProgression(data, cb) @0xC3A278:
                reads an ACTIONS array via EB.Dot.Array(<key>) @0xc3a320, iterates, each element
                -> QuestActionResult..ctor(dict, activeQuest) @0xEA28BC (reads actionType via
                Dot.Integer, actionPos via Dot.Object {x,y}, qid via Dot.String, ...); then reads a
                progression-update object via Dot.Object(<key>) @0xc3a414; ProcessPendingUpdates.
            - then EB.Dot.Object(<teamData key>, data) @0xd65e70 -> QuestsManager.UpdateActiveTeam.
      The LIVE `data` (=response result) was read (QS log) for keys `results`, `progression`,
      `teamData` -- so those are the top-level result keys. With an empty {} result the upstream
      handler found `results`==null and never called ProcessActionResults (AddActionResults' init
      flag @0x2e3c562 read back 0 = never ran), so NO move. This authors all three.

    Action.Type is NOT a plain integer field on the wire. QuestActionResult..ctor reads a nested
    container element["action"], then probes ~11 nested VARIANT keys off it; the FIRST non-null
    variant sets actionType by its slot index (variant "moveto" is slot 1 => MOVE_TO=1, "teleport"
    slot 2, ... in the ctor's priority chain). The chosen variant object then supplies actionPos
    via two Dot.Integer reads keyed "x"/"y", and actionTile = QuestMap.GetTile(actionPos).

    The three literals were resolved live from the running process memory (the il2cpp string-literal
    slots are DOUBLE-indirect: `ldr x8,[slot]; ldr x0,[x8]` -> Il2CppString*): key0="action",
    variant key1="moveto", position keys "x"/"y"."""
    sx, sy = start
    nx, ny = sx + int(offx), sy + int(offy)          # new tile (row, col)

    # A single MOVE_TO action. The exact nested shape the ctor descends:
    #   { "action": { "moveto": { "x": <row>, "y": <col> } } }
    # element["action"]  -> the variant container (x23)
    # ["moveto"]         -> non-null => actionType = MOVE_TO (1)
    # ["x"],["y"]        -> the absolute destination tile => actionPos -> GetTile -> actionTile
    action = {
        "action": {
            "moveto": {"x": nx, "y": ny},
        },
    }
    actions = [action]

    # Arriving at an authored encounter tile is a two-action result: MOVE_TO animates the squad
    # onto the node, then BATTLE makes Gameboard.Action_Battle open the real pre-fight screen.
    # QuestActionResult chooses its enum by the first non-null nested variant; `battle` is slot
    # 3 (BATTLE). Its x/y locate actionTile and `battleEnemy` is deserialized into the
    # encounter entity. The name is live-confirmed from QuestActionResult's field trace. This
    # variant is not final-tile-specific: isFinalBoss is its field, so intermediate nodes use
    # the same slot-3 `battle` variant with isFinalBoss false.
    encounter = QUEST_ENCOUNTERS.get(nx) if ny == QUEST_PATH_COL else None
    if encounter is not None:
        key, is_final_boss, _ = encounter
        actions.append({
            "action": {
                "battle": {
                    "x": nx, "y": ny, "isFinalBoss": is_final_boss,
                    "battleEnemy": build_quest_enemy(
                        key=key, is_final_boss=is_final_boss,
                    ),
                },
            },
        })

    # Updated progression: player now on the new tile; old tile cleared/revealed.
    prog = build_quest_progression(qid, start=(nx, ny), team=team)
    prog["cleared"] = [{"x": sx, "y": sy}]
    prog["revealed"] = [{"x": r, "y": 1} for r in range(QUEST_DIM)]
    if encounter is not None:
        prog.update({
            "currentBattleId": key,
            "currentBattlePos": {"x": nx, "y": ny},
            # This compact identity is the chosen enemy CHARACTER blueprint, not the stable
            # encounter entity key. PrefightScreenData feeds it directly to GetBlueprint;
            # using the encounter id produced live `GETBP story_1_1_1_boss` misses and an
            # empty opponent. Position and health remain sibling progression fields.
            "currentBattleEnemy": {"id": key},
            "currentBattleEnemyHealth": 1.0,
        })
        # QuestProgression and the local QuestUserInfo retain parallel battle state. The
        # pre-fight screen reads the latter through ActiveQuest.localPlayer; progression-only
        # battle fields open the window but leave its fight launch state incomplete.
        prog["users"][LOCAL_UID].update({
            "currentBattleId": key,
            "currentBattlePos": {"x": nx, "y": ny},
            "currentBattleState": "activated",
        })

    # teamData -> QuestsManager.UpdateActiveTeam. Reuse the active-team shape; harmless if unread.
    team_data = build_active_team("%s-0" % qid, heroes=resolve_team(team))

    return {
        # `results` is the AddActionResultsAndUpdateProgression Dot.Array key (live-confirmed);
        # `progression` + `teamData` are the other two top-level result keys it reads.
        "results": actions,
        "progression": prog,
        "teamData": team_data,
    }


# ---------------------------------------------------------------------------
# The player's BASE (the home screen).
#
# The home screen is not a static backdrop: it is a second game board. HomeFlow
# (@0xC5F55C) holds a `BaseBoard` (scene "Baseboard") and fills it from
# QuestsManager.userBase -- an ActiveQuest built by `new ActiveQuest(Base)`
# (@0x109EF6C) out of BaseManager's `Base`, which is nothing but a wrapper around
# an EB.Missions.ActiveMission. So the base uses the SAME Summary + Map machinery
# the STORY board already uses; it just arrives through a different endpoint.
#
# Wire path, all confirmed by disassembly:
#   GET /base/active
#     -> BaseManager.DeserializeData (@0x17343F8) calls
#        BaseSubManager.DeserializeData (@0x173511C) TWICE, with prefix "user" and
#        prefix "alliance". Each key is String.Concat(prefix, <name>) -- there is NO
#        dot separator, so the wire keys are literally `userAvailableBuildings`,
#        `userBuildings`, `userSockets`, `userBase` (an earlier note in
#        TECHNICAL_NOTES spelled these "user.AvailableBuildings"; that is wrong).
#     -> `userBase` is read with Dot.Object and handed to ActiveMission.Deserialize
#        (@0x1514354), whose keys are mode/category/id (all three must be non-empty
#        or the whole parse errors), hash/setName/setId/uid/aid, `data` (the Summary
#        -- note it is `data` here, not `summary`), `map`, `placements`, `modes`.
#     -> Base.get_type (@0x173249C) returns "users" when mission.uid is a VALID Id,
#        else "alliances"; the "users" branch is what makes this the player's own base
#        and selects the `user-base` entry of the missions config as its CommonConfig.
#
# Terrain: GameboardBuilder.BuildInternal (@0xF8B570) sets
#   _ThemeName = summary.theme
#   _ThemeNameFull = summary.theme + "_base"    (when the board is the user's base)
#   library = "library_" + _ThemeNameFull.ToLower()
# so theme "primordial" resolves to `library_primordial_base`, which is exactly the
# `primordial_base` bundle that ships in the APK. Getting the theme wrong yields the
# same missing-material MAGENTA the STORY board showed before session 16.
# ---------------------------------------------------------------------------

BASE_ID = "user_base_1"       # ActiveMission.id -> Base.uniqueId
BASE_THEME = "primordial"     # -> library_primordial_base (see above)
BASE_DIM = 5                  # Map.gridDimension (square grid)

# Sockets (build plots), corrected against EB.Missions.MapTile.Deserialize
# (@0x1484C04, socket loop @0x1485704):
#   * the tile's `sockets` dict ENTRY KEY becomes Socket.id (builder.NewSocket's
#     first arg is key.ToString());
#   * the entry value's `entityType` field becomes Socket.type -- NOT a `type` key
#     (Socket.Deserialize @0x137F434 itself reads only `locked` + base `v`);
#   * tile.sockets is then keyed by socket TYPE (dict.Add uses Socket.type@0x28),
#     which is what Quests.MapTile.Deserialize (@0x1093E9C) looks up with the
#     literal keys "boss"/"tower"/"building"/"relic" to pick bossSocket /
#     towerSocket / buildingSocket. An earlier draft keyed the wire dict by socket
#     id and put the type in a `type` field -- both wrong, the socket was never
#     found and no building could ever attach to a tile.
# `userSockets` (a flat id -> bool map) is the per-player unlock state overlay,
# parsed by BaseSubManager.DeserializeUnlocks (@0x1737CA8).
BASE_SOCKET_TYPE = "building"

# ---------------------------------------------------------------------------
# Buildings.
#
# Wire path (all disassembled):
#   * `userAvailableBuildings` -> BaseSubManager.DeserializeAvailableBuildings
#     (@0x1737168): an ARRAY of dicts. Each: entityType (must be "building" --
#     EB.Base.Builder.NewEntity @0x149B5D4 only takes the Building branch when
#     baseType == "building"; parentEntityType defaults to entityType), then
#     Building.Deserialize (@0x149C594) reads id / name / description / img
#     (Dot.Loc, plain strings fine) / modelId / maxDamage / cost / comingSoon /
#     levels / rank / level / damage / funds{upgrade,repair}. The parsed building
#     lands in builder.availableBuildings keyed by its `id`.
#   * `userBuildings` -> DeserializeOwnedBuildings (@0x17376D0): an ARRAY whose
#     entries are {id, key}: `id` MUST match an available building (TryGetValue
#     into builder.availableBuildings, else "Error deserializing owned
#     buildingId="), the clone re-runs Deserialize on the entry (so rank/level
#     could be overridden here) and is stored keyed by `key`.
#   * The mission's `placements` -> Placement.Deserialize (@0x13A2DDC): a DICT
#     keyed by SOCKET id. Each value: entityType/parentEntityType ("building"),
#     `key` = the building id (passed as NewEntity's extraData, which is what
#     makes the base builder CLONE availableBuildings[key]), `position` = tile
#     coords. Placement.entities is keyed by the outer dict key.
#   * Display: BaseNodeController.Refresh (@0xCF2D30) -> Quests.MapTile
#     .get_building (@0x1094230) = mission.placement.entities[tile.buildingSocket
#     .id] -- so the placements key must equal the tile's socket id -- then loads
#     the prefab named by Building.modelId (@0x78) via GameboardBuilder
#     .LoadBuildingObject ("buildings/prefabs/" + modelId).
#
# modelId therefore must be a child of the `library_buildings` prefab in the
# APK's buildings.assetbundle. The full shipped set (dumped with UnityPy):
#   z_bldg_alliance_help_00..03, z_bldg_away_team_00..03,
#   z_bldg_battle_centre_00..03, z_bldg_gacha_daily_01, z_bldg_gacha_free_01,
#   z_bldg_gacha_other_01
# (the _00.._03 suffix is the visual upgrade tier).
# ---------------------------------------------------------------------------

BASE_BUILDINGS = {
    "bldg_battle_centre": {
        "name": "Battle Centre",
        "desc": "The command centre of your base.",
        "model": "z_bldg_battle_centre_03",
    },
    "bldg_away_team": {
        "name": "Away Team Station",
        "desc": "Coordinates away missions.",
        "model": "z_bldg_away_team_03",
    },
    "bldg_alliance_help": {
        "name": "Alliance Relay",
        "desc": "Call in help from allied Autobots.",
        "model": "z_bldg_alliance_help_03",
    },
    "bldg_crystal_free": {
        "name": "Free Crystal Vault",
        "desc": "Synthesizes a free crystal now and then.",
        "model": "z_bldg_gacha_free_01",
    },
    "bldg_crystal_daily": {
        "name": "Daily Crystal Vault",
        "desc": "Produces one crystal every day.",
        "model": "z_bldg_gacha_daily_01",
    },
    "bldg_crystal_premium": {
        "name": "Premium Crystal Vault",
        "desc": "Stores premium crystals.",
        "model": "z_bldg_gacha_other_01",
    },
}

BASE_PLACEMENTS = {
    (1, 1): "bldg_away_team",        # Back-Left (Away Team Station + Spaceship Shuttle)
    (1, 2): "bldg_battle_centre",    # Back-Center (Battle Centre Command Tower)
    (1, 3): "bldg_alliance_help",    # Back-Right (Alliance Help Radar Tower)
    (2, 1): "bldg_crystal_free",     # Mid-Left (Free Crystal Vault)
    (2, 3): "bldg_crystal_premium",  # Mid-Right (Premium Crystal Vault)
}


def build_base_summary():
    """EB.Missions.Summary for the base, delivered as the mission's `data`.

    Same reader as the STORY mission summary (see build_quest_summary), so the field
    names carry over. `theme` is the one field that must be right: it selects the
    terrain prefab library, and for a base the client appends "_base" to it.
    """
    return {
        "id": BASE_ID, "setId": "", "hash": "b1",
        "category": "base",
        "friendlyName": "Base", "description": "Your base.",
        "energyPerTile": 0, "minXpPerTile": 0, "maxXpPerTile": 0,
        "minHealthPerTile": 0, "maxHealthPerTile": 0,
        "image": "", "theme": BASE_THEME, "todIndex": 0,
    }


def build_base_map():
    """The base's EB.Missions.Map."""
    dim = BASE_DIM
    centre = dim // 2

    def links_for(row, col):
        out = []
        for r, c in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= r < dim and 0 <= c < dim and _base_walkable(r, c):
                out.append({"x": r, "y": c})
        return out

    grid = []
    for row in range(dim):
        r = []
        for col in range(dim):
            if not _base_walkable(row, col):
                r.append({"walkable": False, "hidden": True})
                continue
            lk = links_for(row, col)
            tile = {
                "walkable": True, "hidden": False,
                "lab": "Plot %d-%d" % (row, col),
                "links": lk, "visibleLinks": lk,
                "sockets": {
                    _base_socket_id(row, col): {
                        "entityType": BASE_SOCKET_TYPE,
                        "locked": False,
                    },
                },
            }
            if (row, col) == (centre, centre):
                tile["start"] = True
                tile["lab"] = "Command Centre"
            r.append(tile)
        grid.append(r)

    walkable = sum(1 for row in range(dim) for col in range(dim)
                   if _base_walkable(row, col))
    # Circuit pathways connecting all 3 rows and 3 columns
    path_data = [
        {"path": [{"x": r, "y": c} for c in range(1, 4)]} for r in range(1, 4)
    ] + [
        {"path": [{"x": r, "y": c} for r in range(1, 4)]} for c in range(1, 4)
    ]

    return {
        "hash": "bm_%s" % BASE_ID, "v": 1, "mapHash": "bm_%s" % BASE_ID,
        "gridDimension": dim,
        "grid": grid,
        "walkableCount": walkable,
        "visibleWalkableCount": walkable,
        "pathData": path_data,
        "overrideZoom": 0,
    }


def _base_walkable(row, col):
    """3x3 core grid of plots (rows 1..3, cols 1..3)."""
    return 1 <= row <= 3 and 1 <= col <= 3


def _base_socket_id(row, col):
    return "sock_%d_%d" % (row, col)


def build_base_mission():
    """The EB.Missions.ActiveMission served as `userBase`.

    ActiveMission.Deserialize (@0x1514354) logs an error and gives up unless `mode`,
    `category` and `id` are all non-empty. `uid` must be the local user id: Base.get_type
    keys off `Id.Valid` on it to decide this is a USER base ("users") rather than an
    alliance one, and the "users" answer is what makes ActiveQuest pick UserBaseConfig
    and BaseBoard treat the board as the player's own.
    """
    return {
        "mode": "base", "category": "base", "id": BASE_ID,
        "hash": "b1", "setName": "", "setId": "",
        "uid": LOCAL_UID, "aid": "",
        "modes": ["base"],
        "data": build_base_summary(),
        "map": build_base_map(),
        "placements": {
            _base_socket_id(r, c): {
                "entityType": "building",
                "parentEntityType": "building",
                "key": bid,
                "position": {"x": r, "y": c},
            }
            for (r, c), bid in BASE_PLACEMENTS.items()
        },
    }


def build_base_available_buildings():
    """The building catalogue, one entry per BASE_BUILDINGS row."""
    out = []
    for bid, spec in BASE_BUILDINGS.items():
        out.append({
            "entityType": "building",
            "id": bid,
            "name": spec["name"],
            "description": spec["desc"],
            "img": "",
            "modelId": spec["model"],
            "maxDamage": 100,
            "cost": [],
            "comingSoon": False,
            "levels": [],
            "rank": 1, "level": 1, "damage": 0,
            "funds": {"upgrade": [], "repair": []},
        })
    return out


def build_base_active():
    """GET /base/active reply body (the `result`).

    Only the `user*` half is authored: the alliance sub-manager is fed nothing, so
    BaseSubManager leaves the alliance base null, which is correct offline (there is
    no alliance). The placed buildings appear twice by design: once as owned
    entries here (id + the socket-id `key` they occupy) and once in the mission's
    `placements`, which is the copy the board actually renders from.
    """
    return {
        "userBase": build_base_mission(),
        "userAvailableBuildings": build_base_available_buildings(),
        "userBuildings": [
            {"id": bid, "key": _base_socket_id(r, c)}
            for (r, c), bid in BASE_PLACEMENTS.items()
        ],
        "userSockets": {_base_socket_id(r, c): True
                        for r in range(BASE_DIM) for c in range(BASE_DIM)
                        if _base_walkable(r, c)},
    }


def build_base_hero_details(req_heroes):
    """Dynamic /bcg/getBaseHeroData reply: an ARRAY of computed hero details, one per
    requested hero, drawn from the authored stat curve so the numbers match the roster
    instead of the old crude ad-hoc curve in fakeserver."""
    out = []
    mod_dict = {m["id"]: m for m in _load_mods()}
    relic_dict = {r["id"]: r for r in _load_relics()}
    for h in (req_heroes or []):
        bid = h.get("bid", "")
        rank = int(h.get("rank", 1) or 1)
        level = int(h.get("level", 1) or 1)
        if bid in mod_dict or bid in relic_dict:
            item_info = mod_dict.get(bid) or relic_dict.get(bid)
            star = item_info.get("default_star", 5)
            mdl = item_info.get("model_id", bid)
            hp0, atk0 = _STAR_BASE.get(star, _STAR_BASE[5])
            hp = hp0 * level
            atk = atk0 * level
            out.append({
                "bid": bid, "rank": rank, "level": level,
                "sig_lvl": int(h.get("sig_lvl", 0) or 0),
                "i": art_base(bid), "img": art_base(bid),
                "m": mdl, "mdl": mdl,
                "rating_hp": hp, "max_hp": hp,
                "rating_attack": atk, "attack": atk,
                "health": hp, "armor": 0, "crit_rate": 0, "crit_dmg": 0,
                "block_prof": 0, "perfect_block": 0, "sig_ability": 0,
                "special_attacks": 0, "user_owned": True,
                "mana_gain": _MANA_GAIN_RATE, "mana_start": _DIAG_MANA_START,
                "synergyBonuses": [], "pvpb": {},
            })
        else:
            faction, klass, star = ROSTER.get(bid, ("decepticon", "tact", 5))
            hp, atk = base_stats(bid, rank, level)
            req_sig = h.get("sig_lvl")
            sig_val = int(req_sig) if req_sig is not None else 100
            out.append({
                "bid": bid, "rank": rank, "level": level,
                "sig_lvl": sig_val,
                "i": art_base(bid), "img": art_base(bid),
                "m": model_id(bid), "mdl": model_id(bid),
                "rating_hp": hp, "max_hp": hp,
                "rating_attack": atk, "attack": atk,
                "health": hp, "armor": 0, "crit_rate": 0, "crit_dmg": 0,
                "block_prof": 0, "perfect_block": 0, "sig_ability": 1,
                "special_attacks": max_special_attacks(bid, star), "user_owned": True,
                "mana_gain": _MANA_GAIN_RATE, "mana_start": _DIAG_MANA_START,
                "flvl": 100, "req_fxp": 0, "max_fxp": 100, "mfl": 100,
                "synergyBonuses": [], "pvpb": {},
            })
    return out


def build_responses():
    """Regenerate roster responses and merge authored combat tuning into account data.

    Account data remains otherwise hand-tuned: only its ``missionsconfig`` member is
    replaced, leaving auth, resources, featured-hero, and tutorial data untouched.
    """
    env = lambda result: json.dumps({"error": None, "result": result},
                                     separators=(",", ":"))
    targets = {
        "GET__bcg_getLoginData.json": build_login_data(),
        "GET__bcg_getUserData.json": build_user_data(),
    }
    for fname, result in targets.items():
        path = os.path.join(RESP_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(env(result))
        print(f"wrote {fname}  ({len(OWNED) if 'UserData' in fname else len(ROSTER)} entries)")

    account_path = os.path.join(RESP_DIR, "GET__account_data.json")
    with open(account_path, encoding="utf-8") as f:
        account = json.load(f)
    account["result"]["missionsconfig"] = build_missions_account_data()
    with open(account_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(account, separators=(",", ":")))
    print("updated GET__account_data.json missionsconfig")

    refresh_path = os.path.join(
        RESP_DIR, "GET__autorefresh_missionsconfig_refresh.json"
    )
    with open(refresh_path, "w", encoding="utf-8") as f:
        f.write(env(build_missions_autorefresh_result()))
    print("wrote GET__autorefresh_missionsconfig_refresh.json")


if __name__ == "__main__":
    build_responses()
    print(f"roster: {len(ROSTER)} bots, {len(OWNED)} owned")
