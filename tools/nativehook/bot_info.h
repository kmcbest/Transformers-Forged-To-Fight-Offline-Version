// Auto-generated from Server/tftf_database.db via gamedata.py. DO NOT EDIT DIRECTLY.
#ifndef BOT_INFO_H
#define BOT_INFO_H

typedef struct {
    const char* id;
    int hp;
    int atk;
    int rating;
    float crit_chance;
    float crit_damage;
    const char* klass;
} EnemyStat;

static const EnemyStat ENEMY_STATS[] = {
    { "acidstorm_gs_leader2015", 46620, 2646, 7134, 0.16f, 1.50f, "tech" },
    { "arcee_gs_deluxe2014", 37380, 3612, 7451, 0.16f, 1.50f, "warr" },
    { "barricade_cin_dotm", 36120, 3640, 7373, 0.24f, 1.50f, "scou" },
    { "bitstream_gs_leader2015", 46620, 2646, 7134, 0.16f, 1.50f, "tech" },
    { "blaster_gs_leader2016", 40320, 3199, 7227, 0.16f, 1.50f, "tech" },
    { "bludgeon_gs_rd20", 42420, 3360, 7597, 0.16f, 1.50f, "warr" },
    { "bonecrusher_cin_rotf", 42420, 3234, 7451, 0.16f, 1.50f, "warr" },
    { "breakdown_gs", 37800, 3612, 7487, 0.24f, 1.50f, "scou" },
    { "bumblebee_cin_dotm", 43680, 3108, 7414, 0.16f, 1.50f, "tact" },
    { "bumblebee_gs_kabam", 34020, 3108, 6573, 0.24f, 1.50f, "scou" },
    { "cheetor_bw_transmetal", 36960, 3822, 7658, 0.24f, 1.50f, "scou" },
    { "chromia_gs_kabam", 40740, 3297, 7378, 0.16f, 1.50f, "warr" },
    { "cliffjumper_gs_kabam", 42000, 3388, 7593, 0.16f, 1.50f, "demo" },
    { "cyclonus_gs_uw06", 45780, 3080, 7565, 0.16f, 1.50f, "tact" },
    { "deadend_gs_deluxe2015", 44100, 2989, 7313, 0.16f, 1.50f, "demo" },
    { "dinobot_bw_kabam", 41580, 3269, 7418, 0.16f, 1.50f, "tact" },
    { "dirge_gs_deluxe2008", 41580, 3171, 7305, 0.16f, 1.50f, "warr" },
    { "dragstrip_gs_deluxe2016", 41580, 3171, 7305, 0.16f, 1.50f, "warr" },
    { "drift_cin_aoe", 41580, 3171, 7305, 0.16f, 1.50f, "warr" },
    { "elita_one_gs", 43680, 3108, 7414, 0.16f, 1.50f, "tact" },
    { "fte_optimus_gs_t3", 43680, 3108, 7414, 0.16f, 1.50f, "tact" },
    { "fte_stars_gs_t3", 37800, 2737, 6471, 0.16f, 1.50f, "tact" },
    { "galvatron_gs_voyager2016", 41958, 3388, 7590, 0.16f, 1.50f, "demo" },
    { "grimlock_gs_mp08", 52920, 3360, 8511, 0.08f, 1.30f, "braw" },
    { "grindor_cin_rotf", 47040, 3549, 8219, 0.08f, 1.30f, "braw" },
    { "hotlink_gs_leader2015", 46200, 3626, 8235, 0.08f, 1.30f, "braw" },
    { "hotrod_cin_tlk", 40740, 3297, 7378, 0.16f, 1.50f, "warr" },
    { "hound_cin_tlk", 44520, 3108, 7487, 0.16f, 1.50f, "warr" },
    { "ionstorm_gs_leader2015", 37800, 2737, 6471, 0.16f, 1.50f, "tact" },
    { "ironhide_cin_rotf", 44100, 3017, 7346, 0.16f, 1.50f, "demo" },
    { "ironhide_gs_kabam", 47040, 3549, 8219, 0.08f, 1.30f, "braw" },
    { "jazz_gs_twm05", 37800, 3612, 7487, 0.24f, 1.50f, "scou" },
    { "jetfire_gs_leader2014", 39060, 3052, 6947, 0.16f, 1.50f, "tech" },
    { "kickback_gs_kabam", 35280, 3703, 7373, 0.24f, 1.50f, "scou" },
    { "lifeline_gs_deluxe2014", 38150, 2744, 6511, 0.16f, 1.50f, "tech" },
    { "megatron_cin_rotf", 46200, 2989, 7495, 0.16f, 1.50f, "demo" },
    { "megatron_gs_leader2015", 41580, 3269, 7418, 0.16f, 1.50f, "tact" },
    { "megatronus_gs_kabam", 47460, 3206, 7857, 0.16f, 1.50f, "demo" },
    { "mirage_gs_deluxe2016", 39480, 2891, 6796, 0.16f, 1.50f, "tech" },
    { "mixmaster_cin_rotf", 44100, 2394, 6622, 0.16f, 1.50f, "demo" },
    { "motormaster_gs_voyager2015", 47040, 3549, 8219, 0.08f, 1.30f, "braw" },
    { "necrotronus_gs_kabam", 46620, 3360, 7963, 0.16f, 1.50f, "warr" },
    { "nemesisprime_gs_voyager2015", 45780, 3108, 7597, 0.16f, 1.50f, "tact" },
    { "novastorm_gs_leader2015", 44520, 3017, 7382, 0.16f, 1.50f, "demo" },
    { "optimusprimal_bw_mp32", 46620, 3668, 8321, 0.08f, 1.30f, "braw" },
    { "optimusprime_cin_tf", 47040, 3549, 8219, 0.08f, 1.30f, "braw" },
    { "optimusprime_sg_voyager2015", 47040, 3549, 8219, 0.08f, 1.30f, "braw" },
    { "prowl_gs_deluxe2016", 41160, 3143, 7235, 0.24f, 1.50f, "scou" },
    { "ramjet_gs_deluxe2008", 44520, 3017, 7382, 0.16f, 1.50f, "demo" },
    { "ratchet_gs_kabam", 38150, 2744, 6511, 0.16f, 1.50f, "tech" },
    { "rhinox_gs_voyager2014", 41580, 2772, 6841, 0.16f, 1.50f, "tech" },
    { "rodimusprime_gs_mp09", 46620, 3143, 7711, 0.16f, 1.50f, "tact" },
    { "scorponok_bw_kabam", 45780, 3052, 7532, 0.16f, 1.50f, "warr" },
    { "sharkticon_gs_brawler", 35280, 2667, 6170, 0.08f, 1.30f, "braw" },
    { "sharkticon_gs_demolition", 33110, 2268, 5519, 0.16f, 1.50f, "demo" },
    { "sharkticon_gs_kabam", 27090, 2730, 5531, 0.24f, 1.50f, "scou" },
    { "sharkticon_gs_scout", 27090, 2730, 5531, 0.24f, 1.50f, "scou" },
    { "sharkticon_gs_tactician", 32760, 2331, 5561, 0.16f, 1.50f, "tact" },
    { "sharkticon_gs_tech", 35000, 1988, 5358, 0.16f, 1.50f, "tech" },
    { "sharkticon_gs_warrior", 31850, 2520, 5702, 0.16f, 1.50f, "warr" },
    { "shockwave_gs", 46620, 2646, 7134, 0.16f, 1.50f, "tech" },
    { "sideswipe_gs", 36120, 3640, 7373, 0.24f, 1.50f, "scou" },
    { "skywarp_gs_leader2015", 46620, 2646, 7134, 0.16f, 1.50f, "tech" },
    { "slipstream_gs", 40320, 3612, 7707, 0.24f, 1.50f, "scou" },
    { "soundblaster_gs_mp13b", 37800, 2737, 6471, 0.16f, 1.50f, "tact" },
    { "soundwave_gs", 43260, 2891, 7126, 0.16f, 1.50f, "tech" },
    { "starsaber_gs_leader2014", 43680, 3108, 7414, 0.16f, 1.50f, "tact" },
    { "starscream_ghost_gs", 40320, 3612, 7707, 0.35f, 1.75f, "scou" },
    { "sunstorm_gs_leader2015", 41580, 3171, 7305, 0.16f, 1.50f, "warr" },
    { "sunstreaker_gs_deluxe2008", 46620, 3766, 8435, 0.08f, 1.30f, "braw" },
    { "tantrum_gs_kabam", 46620, 3766, 8435, 0.08f, 1.30f, "braw" },
    { "thrust_gs_deluxe2008", 40320, 3612, 7707, 0.24f, 1.50f, "scou" },
    { "thundercracker_gs_leader2015", 46200, 3626, 8235, 0.08f, 1.30f, "braw" },
    { "ultramagnus_gs_leader", 43680, 3108, 7414, 0.16f, 1.50f, "tact" },
    { "ultramagnus_sg_leader", 47460, 3206, 7857, 0.16f, 1.50f, "demo" },
    { "waspinator_gs_deluxe", 39900, 2954, 6907, 0.16f, 1.50f, "demo" },
    { "wheeljack_gs_mp20", 37380, 2800, 6508, 0.16f, 1.50f, "tech" },
    { "wildrider_gs_deluxe2016", 46620, 3766, 8435, 0.08f, 1.30f, "braw" },
    { "windblade_gs", 36120, 3486, 7194, 0.24f, 1.50f, "scou" },
};
#define NUM_ENEMY_STATS 79

#endif // BOT_INFO_H
