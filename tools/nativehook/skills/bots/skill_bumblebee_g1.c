#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static uint64_t s_bee_last_tick_ms[2] = {0, 0};

static void bumblebee_g1_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_bee_last_tick_ms[player_index] = 0;
    }
}

static void bumblebee_g1_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "bumblebee_gs") == NULL) continue;
        if (s_bee_last_tick_ms[p] == 0) {
            s_bee_last_tick_ms[p] = now_ms;
            continue;
        }
        if (now_ms >= s_bee_last_tick_ms[p] + 1000) {
            s_bee_last_tick_ms[p] = now_ms;
            if (skill_is_in_melee_range(p) || skill_get_opponent_distance(p) <= 6.5f) {
                skill_apply_buff_dur(p, "bumblebee_close_power", 1.5f);
                skill_apply_buff_dur(p, "bumblebee_close_melee", 1.5f);
                skill_add_mana(p, 0.036f);
            }
        }
    }
}

static void bumblebee_g1_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "bumblebee_gs") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (!ctx->is_blocked && skill_has_buff(ap, "bumblebee_sidestep_crit_rate")) {
        skill_consume_buff(ap, "bumblebee_sidestep_crit_rate", 1);
    }

    if (ctx->special_index == 2 && ctx->hit_index == 0) {
        skill_apply_buff_dur(tp, "bumblebee_sp2_power_lock", 10.0f);
    } else if (ctx->special_index == 3 && ctx->is_last_hit) {
        for (int i = 0; i < 20; i++) {
            skill_apply_buff(ap, "bumblebee_sp3_crit_rate");
        }
    }
}

BotSkillModule g_module_bumblebee_g1 = {
    .bot_prefix         = "bumblebee_gs",
    .display_name_zh    = "大黄蜂G1",
    .on_hit_connected   = bumblebee_g1_on_hit_connected,
    .on_simulation_tick = bumblebee_g1_on_simulation_tick,
    .on_fight_reset     = bumblebee_g1_on_fight_reset,
};
