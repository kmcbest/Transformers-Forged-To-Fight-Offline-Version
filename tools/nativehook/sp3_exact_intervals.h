#ifndef SP3_EXACT_INTERVALS_H
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
    { "acidstorm_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "arcee_gs_deluxe2014", 1, {1867, 0, 0, 0}, {3400, 0, 0, 0} },
    { "barricade_cin_dotm", 1, {1867, 0, 0, 0}, {3467, 0, 0, 0} },
    { "bitstream_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "blaster_gs_leader2016", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "bludgeon_gs_rd20", 1, {3100, 0, 0, 0}, {5700, 0, 0, 0} },
    { "bonecrusher_cin_rotf", 1, {1133, 0, 0, 0}, {2633, 0, 0, 0} },
    { "breakdown_gs", 1, {367, 0, 0, 0}, {1900, 0, 0, 0} },
    { "bumblebee_cin_dotm", 1, {1033, 0, 0, 0}, {3833, 0, 0, 0} },
    { "bumblebee_gs_kabam", 1, {100, 0, 0, 0}, {4033, 0, 0, 0} },
    { "cheetor_bw_transmetal", 1, {1933, 0, 0, 0}, {3433, 0, 0, 0} },
    { "chromia_gs_kabam", 1, {4200, 0, 0, 0}, {7400, 0, 0, 0} },
    { "cliffjumper_gs_kabam", 1, {4033, 0, 0, 0}, {5867, 0, 0, 0} },
    { "cyclonus_gs_uw06", 1, {933, 0, 0, 0}, {3367, 0, 0, 0} },
    { "deadend_gs_deluxe2015", 1, {833, 0, 0, 0}, {3633, 0, 0, 0} },
    { "dinobot_bw_kabam", 1, {167, 0, 0, 0}, {5233, 0, 0, 0} },
    { "dirge_gs_deluxe2008", 1, {567, 0, 0, 0}, {7667, 0, 0, 0} },
    { "dragstrip_gs_deluxe2016", 1, {3567, 0, 0, 0}, {5100, 0, 0, 0} },
    { "drift_cin_aoe", 1, {467, 0, 0, 0}, {1700, 0, 0, 0} },
    { "fte_optimus_gs_t3", 1, {1067, 0, 0, 0}, {2500, 0, 0, 0} },
    { "fte_stars_gs_t3", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "galvatron_gs_voyager2016", 1, {4400, 0, 0, 0}, {7200, 0, 0, 0} },
    { "grimlock_gs_mp08", 1, {600, 0, 0, 0}, {6567, 0, 0, 0} },
    { "grindor_cin_rotf", 1, {2633, 0, 0, 0}, {5600, 0, 0, 0} },
    { "hotlink_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "hotrod_cin_tlk", 1, {133, 0, 0, 0}, {2867, 0, 0, 0} },
    { "hound_cin_tlk", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "ionstorm_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "ironhide_cin_rotf", 1, {333, 0, 0, 0}, {3167, 0, 0, 0} },
    { "ironhide_gs_kabam", 1, {4033, 0, 0, 0}, {5867, 0, 0, 0} },
    { "jazz_gs_twm05", 1, {267, 0, 0, 0}, {3000, 0, 0, 0} },
    { "jetfire_gs_leader2014", 1, {2133, 0, 0, 0}, {9567, 0, 0, 0} },
    { "kickback_gs_kabam", 1, {3500, 0, 0, 0}, {8733, 0, 0, 0} },
    { "lifeline_gs_deluxe2014", 1, {1867, 0, 0, 0}, {3400, 0, 0, 0} },
    { "megatron_cin_rotf", 1, {2233, 0, 0, 0}, {4033, 0, 0, 0} },
    { "megatron_gs_leader2015", 1, {2800, 0, 0, 0}, {5567, 0, 0, 0} },
    { "megatronus_gs_kabam", 2, {5100, 7133, 0, 0}, {6700, 7467, 0, 0} },
    { "mirage_gs_deluxe2016", 1, {3567, 0, 0, 0}, {5100, 0, 0, 0} },
    { "mixmaster_cin_rotf", 1, {2133, 0, 0, 0}, {6967, 0, 0, 0} },
    { "motormaster_gs_voyager2015", 1, {4467, 0, 0, 0}, {6233, 0, 0, 0} },
    { "necrotronus_gs_kabam", 2, {5100, 7133, 0, 0}, {6700, 7467, 0, 0} },
    { "nemesisprime_gs_voyager2015", 1, {1067, 0, 0, 0}, {2500, 0, 0, 0} },
    { "novastorm_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "optimusprimal_bw_mp32", 1, {1333, 0, 0, 0}, {7733, 0, 0, 0} },
    { "optimusprime_cin_tf", 1, {1967, 0, 0, 0}, {2867, 0, 0, 0} },
    { "optimusprime_sg_voyager2015", 1, {1067, 0, 0, 0}, {2500, 0, 0, 0} },
    { "prowl_gs_deluxe2016", 1, {3067, 0, 0, 0}, {5333, 0, 0, 0} },
    { "ramjet_gs_deluxe2008", 1, {567, 0, 0, 0}, {7667, 0, 0, 0} },
    { "ratchet_gs_kabam", 1, {4033, 0, 0, 0}, {5867, 0, 0, 0} },
    { "rhinox_gs_voyager2014", 1, {100, 0, 0, 0}, {2000, 0, 0, 0} },
    { "rodimusprime_gs_mp09", 1, {1967, 0, 0, 0}, {2867, 0, 0, 0} },
    { "scorponok_bw_kabam", 1, {1033, 0, 0, 0}, {7067, 0, 0, 0} },
    { "sharkticon_gs_brawler", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "sharkticon_gs_demolition", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "sharkticon_gs_kabam", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "sharkticon_gs_scout", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "sharkticon_gs_tactician", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "sharkticon_gs_tech", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "sharkticon_gs_warrior", 0, {0, 0, 0, 0}, {0, 0, 0, 0} },
    { "shockwave_gs", 1, {3533, 0, 0, 0}, {6067, 0, 0, 0} },
    { "sideswipe_gs", 1, {367, 0, 0, 0}, {1900, 0, 0, 0} },
    { "skywarp_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "slipstream_gs", 1, {1167, 0, 0, 0}, {3600, 0, 0, 0} },
    { "soundblaster_gs_mp13b", 1, {367, 0, 0, 0}, {5700, 0, 0, 0} },
    { "soundwave_gs", 1, {367, 0, 0, 0}, {5700, 0, 0, 0} },
    { "starsaber_gs_leader2014", 1, {2133, 0, 0, 0}, {9567, 0, 0, 0} },
    { "starscream_ghost_gs", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "sunstorm_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "sunstreaker_gs_deluxe2008", 1, {467, 0, 0, 0}, {1700, 0, 0, 0} },
    { "tantrum_gs_kabam", 1, {400, 0, 0, 0}, {6700, 0, 0, 0} },
    { "thrust_gs_deluxe2008", 1, {567, 0, 0, 0}, {7667, 0, 0, 0} },
    { "thundercracker_gs_leader2015", 1, {2000, 0, 0, 0}, {5333, 0, 0, 0} },
    { "ultramagnus_gs_leader", 1, {2000, 0, 0, 0}, {5733, 0, 0, 0} },
    { "ultramagnus_sg_leader", 1, {2000, 0, 0, 0}, {5733, 0, 0, 0} },
    { "waspinator_gs_deluxe", 2, {1600, 6400, 0, 0}, {2633, 8000, 0, 0} },
    { "wheeljack_gs_mp20", 1, {267, 0, 0, 0}, {2367, 0, 0, 0} },
    { "wildrider_gs_deluxe2016", 1, {3067, 0, 0, 0}, {5333, 0, 0, 0} },
    { "windblade_gs", 1, {1167, 0, 0, 0}, {3600, 0, 0, 0} },
};

#define NUM_SP3_EXACT_INTERVALS 78

static inline const SP3BotInterval* sp3_find_exact_interval(const char* bot_id) {
    if (!bot_id || !bot_id[0]) return NULL;
    for (int i = 0; i < NUM_SP3_EXACT_INTERVALS; i++) {
        if (strcmp(G_SP3_EXACT_INTERVALS[i].bot_id, bot_id) == 0) {
            return &G_SP3_EXACT_INTERVALS[i];
        }
    }
    // Substring fallback
    for (int i = 0; i < NUM_SP3_EXACT_INTERVALS; i++) {
        if (strstr(bot_id, G_SP3_EXACT_INTERVALS[i].bot_id) || strstr(G_SP3_EXACT_INTERVALS[i].bot_id, bot_id)) {
            return &G_SP3_EXACT_INTERVALS[i];
        }
    }
    return NULL;
}

#endif // SP3_EXACT_INTERVALS_H
