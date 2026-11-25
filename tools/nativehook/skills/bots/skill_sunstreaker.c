#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static int s_sunstreaker_unstop_used[2] = {0, 0};

static void sunstreaker_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_sunstreaker_unstop_used[player_index] = 0;
    }
}

static void sunstreaker_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "sunstreaker") == NULL) continue;
        float hp_r = skill_get_hp_ratio(p);
        if (!s_sunstreaker_unstop_used[p] && hp_r > 0.0f && hp_r <= 0.40f) {
            s_sunstreaker_unstop_used[p] = 1;
            skill_set_unstoppable(p, 5000);
            skill_apply_buff_dur(p, "sunstreaker_low_hp_unstoppable", 5.0f);
            skill_apply_buff_dur(p, "sunstreaker_low_hp_unstoppable_vfx", 5.0f);
            skill_log("SUNSTREAKER: P%d HP <= 40%% -> granted Unstoppable (5.0s)", p);
        }
    }
}

BotSkillModule g_module_sunstreaker = {
    .bot_prefix         = "sunstreaker",
    .display_name_zh    = "飞毛腿",
    .on_simulation_tick = sunstreaker_on_simulation_tick,
    .on_fight_reset     = sunstreaker_on_fight_reset,
};
