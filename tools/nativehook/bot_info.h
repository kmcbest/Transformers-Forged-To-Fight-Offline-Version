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
    { "acidstorm_gs_leader2015", 36950, 2755, 6419, 0.16f, 1.50f, "tech" },
    { "arcee_gs_deluxe2014", 43750, 3070, 7376, 0.16f, 1.50f, "warr" },
    { "barricade_cin_dotm", 40250, 3040, 7036, 0.24f, 1.50f, "scou" },
    { "bitstream_gs_leader2015", 37400, 2770, 6475, 0.16f, 1.50f, "tech" },
    { "blaster_gs_leader2016", 37850, 2780, 6526, 0.16f, 1.50f, "tech" },
    { "bludgeon_gs_rd20", 44820, 3040, 7434, 0.16f, 1.50f, "warr" },
    { "bonecrusher_cin_rotf", 45450, 2965, 7402, 0.16f, 1.50f, "warr" },
    { "breakdown_gs", 40150, 3020, 7005, 0.24f, 1.50f, "scou" },
    { "bumblebee_cin_dotm", 37100, 2810, 6495, 0.16f, 1.50f, "tact" },
    { "bumblebee_gs_kabam", 39400, 2960, 6870, 0.24f, 1.50f, "scou" },
    { "cheetor_bw_transmetal", 39200, 3085, 6997, 0.24f, 1.50f, "scou" },
    { "chromia_gs_kabam", 44500, 2985, 7344, 0.16f, 1.50f, "warr" },
    { "cliffjumper_gs_kabam", 44300, 3060, 7413, 0.16f, 1.50f, "demo" },
    { "cyclonus_gs_uw06", 38100, 2740, 6501, 0.16f, 1.50f, "tact" },
    { "deadend_gs_deluxe2015", 44150, 3040, 7376, 0.16f, 1.50f, "demo" },
    { "dinobot_bw_kabam", 37600, 2790, 6515, 0.16f, 1.50f, "tact" },
    { "dirge_gs_deluxe2008", 44950, 2945, 7336, 0.16f, 1.50f, "warr" },
    { "dragstrip_gs_deluxe2016", 44100, 3050, 7384, 0.16f, 1.50f, "warr" },
    { "drift_cin_aoe", 44250, 3060, 7408, 0.16f, 1.50f, "warr" },
    { "fte_optimus_gs_t3", 38400, 2780, 6574, 0.16f, 1.50f, "tact" },
    { "fte_stars_gs_t3", 37251, 2669, 6345, 0.16f, 1.50f, "tact" },
    { "galvatron_gs_voyager2016", 46250, 3085, 7612, 0.16f, 1.50f, "demo" },
    { "grimlock_gs_mp08", 46320, 3465, 8058, 0.08f, 1.30f, "braw" },
    { "grindor_cin_rotf", 45720, 3480, 8023, 0.08f, 1.30f, "braw" },
    { "hotlink_gs_leader2015", 44920, 3525, 8007, 0.08f, 1.30f, "braw" },
    { "hotrod_cin_tlk", 43900, 3080, 7401, 0.16f, 1.50f, "warr" },
    { "hound_cin_tlk", 44665, 3089, 7477, 0.16f, 1.50f, "warr" },
    { "ionstorm_gs_leader2015", 36950, 2755, 6419, 0.16f, 1.50f, "tact" },
    { "ironhide_cin_rotf", 45850, 3045, 7530, 0.16f, 1.50f, "demo" },
    { "ironhide_gs_kabam", 44620, 3470, 7917, 0.08f, 1.30f, "braw" },
    { "jazz_gs_twm05", 39600, 3075, 7020, 0.24f, 1.50f, "scou" },
    { "jetfire_gs_leader2014", 38250, 2795, 6578, 0.16f, 1.50f, "tech" },
    { "kickback_gs_kabam", 40650, 3080, 7118, 0.24f, 1.50f, "scou" },
    { "lifeline_gs_deluxe2014", 37150, 2740, 6419, 0.16f, 1.50f, "tech" },
    { "megatron_cin_rotf", 45512, 2911, 7346, 0.16f, 1.50f, "demo" },
    { "megatron_gs_leader2015", 38250, 2795, 6578, 0.16f, 1.50f, "tact" },
    { "megatronus_gs_kabam", 46753, 3123, 7700, 0.16f, 1.50f, "demo" },
    { "mirage_gs_deluxe2016", 37640, 2821, 6555, 0.16f, 1.50f, "tech" },
    { "mixmaster_cin_rotf", 44750, 2965, 7342, 0.16f, 1.50f, "demo" },
    { "motormaster_gs_voyager2015", 45380, 3515, 8035, 0.08f, 1.30f, "braw" },
    { "necrotronus_gs_kabam", 46150, 3075, 7592, 0.16f, 1.50f, "warr" },
    { "nemesisprime_gs_voyager2015", 38200, 2785, 6561, 0.16f, 1.50f, "tact" },
    { "novastorm_gs_leader2015", 45200, 2980, 7398, 0.16f, 1.50f, "demo" },
    { "optimusprimal_bw_mp32", 45927, 3578, 8156, 0.08f, 1.30f, "braw" },
    { "optimusprime_cin_tf", 46340, 3457, 8052, 0.08f, 1.30f, "braw" },
    { "optimusprime_sg_voyager2015", 45150, 3495, 7992, 0.08f, 1.30f, "braw" },
    { "prowl_gs_deluxe2016", 40556, 3063, 7090, 0.24f, 1.50f, "scou" },
    { "ramjet_gs_deluxe2008", 43857, 2942, 7238, 0.16f, 1.50f, "demo" },
    { "ratchet_gs_kabam", 37651, 2668, 6379, 0.16f, 1.50f, "tech" },
    { "rhinox_gs_voyager2014", 38450, 2715, 6502, 0.16f, 1.50f, "tech" },
    { "rodimusprime_gs_mp09", 37800, 2770, 6509, 0.16f, 1.50f, "tact" },
    { "scorponok_bw_kabam", 45100, 2972, 7381, 0.16f, 1.50f, "warr" },
    { "sharkticon_gs_brawler", 44780, 3445, 7902, 0.08f, 1.30f, "braw" },
    { "sharkticon_gs_demolition", 44550, 2995, 7359, 0.16f, 1.50f, "demo" },
    { "sharkticon_gs_kabam", 39900, 2970, 6925, 0.24f, 1.50f, "scou" },
    { "sharkticon_gs_scout", 40300, 2990, 6983, 0.24f, 1.50f, "scou" },
    { "sharkticon_gs_tactician", 37350, 2735, 6430, 0.16f, 1.50f, "tact" },
    { "sharkticon_gs_tech", 37300, 2735, 6425, 0.16f, 1.50f, "tech" },
    { "sharkticon_gs_warrior", 44700, 2990, 7366, 0.16f, 1.50f, "warr" },
    { "shockwave_gs", 38600, 2825, 6643, 0.16f, 1.50f, "tech" },
    { "sideswipe_gs", 39800, 3050, 7009, 0.24f, 1.50f, "scou" },
    { "skywarp_gs_leader2015", 37200, 2765, 6451, 0.16f, 1.50f, "tech" },
    { "slipstream_gs", 40800, 2980, 7015, 0.24f, 1.50f, "scou" },
    { "soundblaster_gs_mp13b", 37450, 2765, 6473, 0.16f, 1.50f, "tact" },
    { "soundwave_gs", 38100, 2760, 6524, 0.16f, 1.50f, "tech" },
    { "starsaber_gs_leader2014", 37900, 2775, 6525, 0.16f, 1.50f, "tact" },
    { "starscream_ghost_gs", 41100, 3060, 7134, 0.35f, 1.75f, "scou" },
    { "sunstorm_gs_leader2015", 45300, 2950, 7372, 0.16f, 1.50f, "warr" },
    { "sunstreaker_gs_deluxe2008", 44250, 3560, 7988, 0.08f, 1.30f, "braw" },
    { "tantrum_gs_kabam", 44850, 3590, 8076, 0.08f, 1.30f, "braw" },
    { "thrust_gs_deluxe2008", 40400, 2950, 6945, 0.24f, 1.50f, "scou" },
    { "thundercracker_gs_leader2015", 45514, 3531, 8066, 0.08f, 1.30f, "braw" },
    { "ultramagnus_gs_leader", 38500, 2760, 6559, 0.16f, 1.50f, "tact" },
    { "ultramagnus_sg_leader", 45650, 3025, 7489, 0.16f, 1.50f, "demo" },
    { "waspinator_gs_deluxe", 43800, 2955, 7247, 0.16f, 1.50f, "demo" },
    { "wheeljack_gs_mp20", 36838, 2729, 6378, 0.16f, 1.50f, "tech" },
    { "wildrider_gs_deluxe2016", 44380, 3545, 7983, 0.08f, 1.30f, "braw" },
    { "windblade_gs", 39100, 3070, 6971, 0.24f, 1.50f, "scou" },
};
#define NUM_ENEMY_STATS 78

#endif // BOT_INFO_H
