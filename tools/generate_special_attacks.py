#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_special_attacks.py
Generates tools/nativehook/special_attacks_zh.h from:
1. assets/xlate/snapshots/zh-CN/special_attacks_zh-CN.json (Official snapshot)
2. Built-in base APK translation asset (if available)
3. assets/xlate/custom_special_attacks.json (User-defined custom translations)

Applies full combinatorial alias expansion (MS_, _GS, MOVE_..._SPECIAL, FTE_, etc.)
and outputs a strictly strcmp-ordered C lookup table with bsearch.
"""

import os
import sys
import json
import zipfile
from pathlib import Path

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "assets/xlate/snapshots/zh-CN/special_attacks_zh-CN.json"
CUSTOM_PATH = ROOT / "assets/xlate/custom_special_attacks.json"
BASE_APK_PATH = ROOT / "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk"
OUTPUT_HEADER_PATH = ROOT / "tools/nativehook/special_attacks_zh.h"


def escape_c_string(s: str) -> str:
    out = []
    for c in s:
        if c == '\\':
            out.append('\\\\')
        elif c == '"':
            out.append('\\"')
        elif c == '\n':
            out.append('\\n')
        elif c == '\r':
            out.append('\\r')
        elif c == '\t':
            out.append('\\t')
        else:
            out.append(c)
    return "".join(out)


def load_translations():
    table = {}

    # 1. Base APK built-in translation (if present)
    if BASE_APK_PATH.exists():
        try:
            with zipfile.ZipFile(BASE_APK_PATH, 'r') as z:
                bdata = z.read('assets/bin/Data/553a7fd23d0ff48eb90bc096bfec3319')
            jstart = bdata.find(b'{', bdata.find(b'special_attacks_zh-CN'))
            if jstart != -1:
                builtin = json.loads(bdata[jstart:bdata.rfind(b'}')+1].decode('utf-8', errors='ignore'))
                for s in builtin.get('strings', []):
                    table[s['k']] = s['v']
                print(f"Loaded {len(table)} strings from base APK.")
        except Exception as e:
            print(f"Warning: Could not read built-in APK translation: {e}")

    # 2. Official snapshot (overrides base APK)
    if SNAPSHOT_PATH.exists():
        with open(SNAPSHOT_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            snap = json.load(f)
        for s in snap.get('strings', []):
            table[s['k']] = s['v']
        print(f"Loaded strings from official snapshot (total: {len(table)}).")

    # 3. User-defined custom special attacks (takes highest priority)
    if CUSTOM_PATH.exists():
        with open(CUSTOM_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            custom = json.load(f)

        # A. bots dict
        bots = custom.get('bots', {})
        for bot_id, bdata in bots.items():
            b_upper = bot_id.upper()
            specials = bdata.get('specials', [])
            for idx, sp in enumerate(specials):
                name = sp.get('name', '')
                desc = sp.get('desc', '')
                if name:
                    for key_fmt in [
                        f"ID_SPECIAL_ATTACK_{b_upper}_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_{b_upper}_{idx}",
                        f"ID_SPECIAL_ATTACK_{b_upper}_GS_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_{b_upper}_GS_{idx}",
                        f"ID_SPECIAL_ATTACK_MOVE_{b_upper}_SPECIAL_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_MOVE_{b_upper}_SPECIAL_{idx}",
                        f"ID_SPECIAL_ATTACK_MOVE_{b_upper}_GS_SPECIAL_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_MOVE_{b_upper}_GS_SPECIAL_{idx}",
                    ]:
                        table[key_fmt] = name
                if desc:
                    for key_fmt in [
                        f"ID_SPECIAL_ATTACK_DESCRIPTION_{b_upper}_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_DESCRIPTION_{b_upper}_{idx}",
                        f"ID_SPECIAL_ATTACK_DESCRIPTION_{b_upper}_GS_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_DESCRIPTION_{b_upper}_GS_{idx}",
                        f"ID_SPECIAL_ATTACK_DESCRIPTION_MOVE_{b_upper}_SPECIAL_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_DESCRIPTION_MOVE_{b_upper}_SPECIAL_{idx}",
                        f"ID_SPECIAL_ATTACK_DESCRIPTION_MOVE_{b_upper}_GS_SPECIAL_{idx}",
                        f"MS_ID_SPECIAL_ATTACK_DESCRIPTION_MOVE_{b_upper}_GS_SPECIAL_{idx}",
                    ]:
                        table[key_fmt] = desc

        # B. raw keys dict
        raw_keys = custom.get('raw_keys', {})
        for k, v in raw_keys.items():
            if not k.startswith('//') and isinstance(v, str):
                table[k] = v
                if k.startswith('MS_'):
                    table[k[3:]] = v
                else:
                    table['MS_' + k] = v

        print(f"Loaded custom translations for {len(bots)} bots.")

    return table


def expand_aliases(table: dict) -> dict:
    expanded = dict(table)

    # 1. Ensure MS_ symmetry
    for k, v in list(expanded.items()):
        if k.startswith('MS_'):
            non_ms = k[3:]
            if non_ms not in expanded:
                expanded[non_ms] = v
        else:
            ms = 'MS_' + k
            if ms not in expanded:
                expanded[ms] = v

    # 2. _GS Suffix Expansion:
    # If a key has _GS_, generate the non-_GS variant (fixes Soundwave, Shockwave, Sideswipe, Starscream, Windblade, Slipstream!)
    for k, v in list(expanded.items()):
        if '_GS_' in k:
            non_gs = k.replace('_GS_', '_')
            if non_gs not in expanded:
                expanded[non_gs] = v

    # 3. Known Bot Name Aliases
    aliases = [
        ('BLUDGE', 'BLUDGEON'),
        ('BLUDGEON', 'BLUDGE'),
        ('WASP', 'WASPINATOR'),
        ('WASPINATOR', 'WASP'),
        ('RATCH', 'RATCHET'),
        ('RATCHET', 'RATCH'),
        ('WINDB', 'WINDBLADE'),
        ('WINDBLADE', 'WINDB'),
        ('CLIFFJUMP', 'CLIFFJUMPER'),
        ('CLIFFJUMPER', 'CLIFFJUMP'),
        ('NECROTRO', 'NECROTRONUS'),
        ('NECROTRONUS', 'NECROTRO'),
        ('NEMESIS', 'NEMESISPRIME'),
        ('NEMESISPRIME', 'NEMESIS'),
        ('SOUND', 'SOUNDWAVE'),
        ('SOUNDWAVE', 'SOUND'),
        ('SOUND', 'SOUNDBLASTER'),
        ('SOUNDBLASTER', 'SOUND'),
        ('SHOCK', 'SHOCKWAVE'),
        ('SHOCKWAVE', 'SHOCK'),
        ('SIDES', 'SIDESWIPE'),
        ('SIDESWIPE', 'SIDES'),
        ('STARS', 'STARSCREAM'),
        ('STARSCREAM', 'STARS'),
        ('OPTIMUS', 'OPTIMUSPRIME'),
        ('OPTIMUSPRIME', 'OPTIMUS'),
        ('OPTIMUS', 'OPTIMUSPRIME_GS'),
        ('OPTIMUS_GS', 'OPTIMUSPRIME_GS_V'),
        ('OPTIMUS_GS', 'FTE_OPTIMUS_GS'),
        ('STARS_GS', 'FTE_STARS_GS'),
        ('SUNSTREAK', 'SUNSTREAKER'),
        ('SUNSTREAKER', 'SUNSTREAK'),
        ('SOUNDBLAST', 'SOUNDBLASTER'),
        ('SOUNDBLASTER', 'SOUNDBLAST'),
        ('MOTORMASTER', 'MOTOMASTER'),
        ('MOTOMASTER', 'MOTORMASTER'),
        ('OPTIMUSPRIME_SG', 'OPTIMUS_SG'),
        ('OPTIMUS_SG', 'OPTIMUSPRIME_SG'),
    ]

    for src, dst in aliases:
        for k, v in list(expanded.items()):
            if f'_{src}_' in k:
                new_k = k.replace(f'_{src}_', f'_{dst}_')
                if new_k not in expanded:
                    expanded[new_k] = v

    # 4. MOVE_..._SPECIAL Variants:
    # For any key like ID_SPECIAL_ATTACK_NAME_IDX or ID_SPECIAL_ATTACK_DESCRIPTION_NAME_IDX,
    # generate ID_SPECIAL_ATTACK_MOVE_NAME_SPECIAL_IDX and ID_SPECIAL_ATTACK_MOVE_NAME_GS_SPECIAL_IDX
    prefixes = [
        ("MS_ID_SPECIAL_ATTACK_DESCRIPTION_", "MS_ID_SPECIAL_ATTACK_DESCRIPTION_MOVE_", "_SPECIAL_"),
        ("ID_SPECIAL_ATTACK_DESCRIPTION_", "ID_SPECIAL_ATTACK_DESCRIPTION_MOVE_", "_SPECIAL_"),
        ("MS_ID_SPECIAL_ATTACK_", "MS_ID_SPECIAL_ATTACK_MOVE_", "_SPECIAL_"),
        ("ID_SPECIAL_ATTACK_", "ID_SPECIAL_ATTACK_MOVE_", "_SPECIAL_"),
    ]

    for k, v in list(expanded.items()):
        for pref, new_pref, mid in prefixes:
            if k.startswith(pref) and not k.startswith(new_pref):
                rest = k[len(pref):]
                if '_' in rest:
                    name_part, idx_part = rest.rsplit('_', 1)
                    if idx_part.isdigit():
                        k_move = f"{new_pref}{name_part}{mid}{idx_part}"
                        if k_move not in expanded:
                            expanded[k_move] = v
                        # If name_part ends with _GS, also generate without _GS
                        if name_part.endswith('_GS'):
                            base_name = name_part[:-3]
                            k_move_base = f"{new_pref}{base_name}{mid}{idx_part}"
                            if k_move_base not in expanded:
                                expanded[k_move_base] = v
                        else:
                            k_move_gs = f"{new_pref}{name_part}_GS{mid}{idx_part}"
                            if k_move_gs not in expanded:
                                expanded[k_move_gs] = v
                break

    # 5. Final MS_ check after all expansions
    for k, v in list(expanded.items()):
        if k.startswith('MS_'):
            non_ms = k[3:]
            if non_ms not in expanded:
                expanded[non_ms] = v
        else:
            ms = 'MS_' + k
            if ms not in expanded:
                expanded[ms] = v

    return expanded


def main():
    print("[*] Generating special attacks localization header...")
    raw_table = load_translations()
    full_table = expand_aliases(raw_table)

    # Sort strictly by strcmp order
    sorted_items = sorted(full_table.items(), key=lambda item: item[0].encode('utf-8'))

    lines = [
        "/* Generated by generate_special_attacks.py - DO NOT EDIT MANUALLY */",
        "#ifndef SPECIAL_ATTACKS_ZH_H",
        "#define SPECIAL_ATTACKS_ZH_H",
        "",
        "#include <stdlib.h>",
        "#include <string.h>",
        "",
        "struct SpecialAttackLocEntry {",
        "    const char* k;",
        "    const char* v;",
        "};",
        "",
        "static const struct SpecialAttackLocEntry SPECIAL_ATTACKS_ZH[] = {"
    ]

    for k, v in sorted_items:
        ek = escape_c_string(k)
        ev = escape_c_string(v)
        lines.append(f'    {{ "{ek}", "{ev}" }},')

    lines.extend([
        "};",
        f"#define NUM_SPECIAL_ATTACKS_ZH (sizeof(SPECIAL_ATTACKS_ZH) / sizeof(SPECIAL_ATTACKS_ZH[0]))",
        "",
        "static int cmp_special_attack_loc(const void* a, const void* b) {",
        "    const char* key = (const char*)a;",
        "    const struct SpecialAttackLocEntry* entry = (const struct SpecialAttackLocEntry*)b;",
        "    return strcmp(key, entry->k);",
        "}",
        "",
        "static const char* lookup_special_attack_zh(const char* key) {",
        "    if (!key || !*key) return NULL;",
        "    const struct SpecialAttackLocEntry* res = (const struct SpecialAttackLocEntry*)bsearch(",
        "        key,",
        "        SPECIAL_ATTACKS_ZH,",
        "        NUM_SPECIAL_ATTACKS_ZH,",
        "        sizeof(struct SpecialAttackLocEntry),",
        "        cmp_special_attack_loc",
        "    );",
        "    if (res) return res->v;",
        "    return NULL;",
        "}",
        "",
        "#endif /* SPECIAL_ATTACKS_ZH_H */",
        ""
    ])

    OUTPUT_HEADER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HEADER_PATH, 'w', encoding='utf-8', errors='ignore') as f:
        f.write("\n".join(lines))

    print(f"[+] Successfully generated {OUTPUT_HEADER_PATH} with {len(sorted_items)} entries.")


if __name__ == "__main__":
    main()
