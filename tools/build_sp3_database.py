import json

with open("tools/complete_sp3_intervals.json", "r", encoding="utf-8") as f:
    stage_data = json.load(f)

with open("Server/sp3_timings.json", "r", encoding="utf-8") as f:
    server_timings = json.load(f)

# Helper to find intervals from stage_data
def get_ivs(key_pattern):
    for sname, sinfo in stage_data.items():
        if key_pattern.lower() in sname.lower() or key_pattern.lower() in sinfo["actor0"].lower():
            return [[int(round(s * 1000)), int(round(e * 1000))] for s, e in sinfo["intervals"]]
    return None

# Explicit mapping of each bot to its true base stage
bot_to_stage = {
    "acidstorm_gs_leader2015": "StarScream_GS",
    "arcee_gs_deluxe2014": "Arcee_gs",
    "barricade_cin_dotm": "Barricade_Cin",
    "bitstream_gs_leader2015": "StarScream_GS",
    "blaster_gs_leader2016": "Blaster_GS",
    "bludgeon_gs_rd20": "Bludgeon_Special3",
    "bonecrusher_cin_rotf": "Bonecrusher_Special03",
    "breakdown_gs": "Sideswipe_GS",
    "bumblebee_cin_dotm": "Bumblebee_Cin",
    "bumblebee_gs_kabam": "Bumblebee_GS_attack",
    "cheetor_bw_transmetal": "Cheetor_BW",
    "chromia_gs_kabam": "chromia_gs",
    "cliffjumper_gs_kabam": "Cliffjumper_GS",
    "cyclonus_gs_uw06": "Cyclonus_gs",
    "deadend_gs_deluxe2015": "deadend_gs",
    "dinobot_bw_kabam": "Dinobot_bw",
    "dirge_gs_deluxe2008": "Dirge_GS",
    "dragstrip_gs_deluxe2016": "Mirage_Special03",
    "drift_cin_aoe": "Drift_Cin",
    "fte_optimus_gs_t3": "OptimusPrime_GSV",
    "fte_stars_gs_t3": "StarScream_GS",
    "galvatron_gs_voyager2016": "Galvatron_GS",
    "grimlock_gs_mp08": "Grimlock_Special03",
    "grindor_cin_rotf": "Grindor_Special03",
    "hotlink_gs_leader2015": "StarScream_GS",
    "hotrod_cin_tlk": "Hotrod_cin",
    "hound_cin_tlk": "Hound_Cin",
    "ionstorm_gs_leader2015": "StarScream_GS",
    "ironhide_cin_rotf": "Ironhide_Special03",
    "ironhide_gs_kabam": "Ironhide_GS_Special03",
    "jazz_gs_twm05": "Jazz_GS",
    "jetfire_gs_leader2014": "Jetfire_GS",
    "kickback_gs_kabam": "Kickback_Special03",
    "lifeline_gs_deluxe2014": "Arcee_gs",
    "megatron_cin_rotf": "Megatron_Cin",
    "megatron_gs_leader2015": "Megatron_GS",
    "megatronus_gs_kabam": "Megatronus_gs",
    "mirage_gs_deluxe2016": "Mirage_Special03",
    "mixmaster_cin_rotf": "Mixmaster_Cin",
    "motormaster_gs_voyager2015": "Motormaster_GS",
    "necrotronus_gs_kabam": "Necrotronus_GS",
    "nemesisprime_gs_voyager2015": "OptimusPrime_GSV",
    "novastorm_gs_leader2015": "StarScream_GS",
    "optimusprimal_bw_mp32": "OptimusPrimal_BW",
    "optimusprime_cin_tf": "OptimusPrime_Cin",
    "optimusprime_sg_voyager2015": "OptimusPrime_GSV",
    "prowl_gs_deluxe2016": "Prowl_Special03",
    "ramjet_gs_deluxe2008": "Ramjet_GS",
    "ratchet_gs_kabam": "Ratchet_GS",
    "rhinox_gs_voyager2014": "Rhinox_gs",
    "rodimusprime_gs_mp09": "Rodimus_GS",
    "scorponok_bw_kabam": "Scorponok_BW",
    "sharkticon_gs_brawler": "Sharkticon",
    "sharkticon_gs_demolition": "Sharkticon",
    "sharkticon_gs_kabam": "Sharkticon",
    "sharkticon_gs_scout": "Sharkticon",
    "sharkticon_gs_tactician": "Sharkticon",
    "sharkticon_gs_tech": "Sharkticon",
    "sharkticon_gs_warrior": "Sharkticon",
    "shockwave_gs": "Shockwave_GS",
    "sideswipe_gs": "Sideswipe_GS",
    "skywarp_gs_leader2015": "Skywarp_GS",
    "slipstream_gs": "slipstream_gs",
    "soundblaster_gs_mp13b": "Soundblast_GS",
    "soundwave_gs": "Soundwave_GS",
    "starsaber_gs_leader2014": "Jetfire_GS",
    "starscream_ghost_gs": "StarScream_GS",
    "sunstorm_gs_leader2015": "StarScream_GS",
    "sunstreaker_gs_deluxe2008": "Sunstreak_Special3",
    "tantrum_gs_kabam": "Tantrum_gs",
    "thrust_gs_deluxe2008": "Ramjet_GS",
    "thundercracker_gs_leader2015": "Thundercracker_GS",
    "ultramagnus_gs_leader": "UltraMagnus_GS",
    "ultramagnus_sg_leader": "UltraMagnus_GS",
    "waspinator_gs_deluxe": "Waspinator_BW",
    "wheeljack_gs_mp20": "Wheeljack_gs",
    "wildrider_gs_deluxe2016": "Prowl_Special03",
    "windblade_gs": "windblade_gs"
}

updated_server_timings = dict(server_timings)

all_c_entries = []

for bot_id, stg_pattern in sorted(bot_to_stage.items()):
    ivs = get_ivs(stg_pattern)
    if ivs is None:
        print(f"WARNING: pattern {stg_pattern} not found for {bot_id}!")
        ivs = []
    
    # Update JSON
    if bot_id in updated_server_timings:
        updated_server_timings[bot_id]["intervals"] = ivs
    else:
        updated_server_timings[bot_id] = {
            "intervals": ivs,
            "props": {},
            "notes": f"Auto-mapped from {stg_pattern}"
        }
        
    # Prepare C entry
    all_c_entries.append((bot_id, ivs))

print(f"Total mapped bots: {len(all_c_entries)}")

# Save updated Server/sp3_timings.json
with open("Server/sp3_timings.json", "w", encoding="utf-8") as f:
    json.dump(updated_server_timings, f, indent=2, ensure_ascii=False)
print("Updated Server/sp3_timings.json successfully!")

# Generate tools/nativehook/sp3_exact_intervals.h
header_content = """#ifndef SP3_EXACT_INTERVALS_H
#define SP3_EXACT_INTERVALS_H

#include <stdint.h>
#include <string.h>

typedef struct {
    const char* bot_id;
    int count;
    int on_ms[4];
    int off_ms[4];
} SP3BotInterval;

static const SP3BotInterval G_SP3_EXACT_INTERVALS[] = {
"""

for bot_id, ivs in all_c_entries:
    cnt = len(ivs)
    ons = [0, 0, 0, 0]
    offs = [0, 0, 0, 0]
    for i, (on, off) in enumerate(ivs[:4]):
        ons[i] = on
        offs[i] = off
    header_content += f'    {{ "{bot_id}", {cnt}, {{{ons[0]}, {ons[1]}, {ons[2]}, {ons[3]}}}, {{{offs[0]}, {offs[1]}, {offs[2]}, {offs[3]}}} }},\n'

header_content += f"""}};

#define NUM_SP3_EXACT_INTERVALS {len(all_c_entries)}

static inline const SP3BotInterval* sp3_find_exact_interval(const char* bot_id) {{
    if (!bot_id || !bot_id[0]) return NULL;
    for (int i = 0; i < NUM_SP3_EXACT_INTERVALS; i++) {{
        if (strcmp(G_SP3_EXACT_INTERVALS[i].bot_id, bot_id) == 0) {{
            return &G_SP3_EXACT_INTERVALS[i];
        }}
    }}
    // Substring fallback
    for (int i = 0; i < NUM_SP3_EXACT_INTERVALS; i++) {{
        if (strstr(bot_id, G_SP3_EXACT_INTERVALS[i].bot_id) || strstr(G_SP3_EXACT_INTERVALS[i].bot_id, bot_id)) {{
            return &G_SP3_EXACT_INTERVALS[i];
        }}
    }}
    return NULL;
}}

#endif // SP3_EXACT_INTERVALS_H
"""

with open("tools/nativehook/sp3_exact_intervals.h", "w", encoding="utf-8") as f:
    f.write(header_content)
print("Generated tools/nativehook/sp3_exact_intervals.h successfully!")
