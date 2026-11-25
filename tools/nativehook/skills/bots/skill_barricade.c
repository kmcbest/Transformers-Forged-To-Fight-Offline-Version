#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static uint64_t s_knockdown_standup_ms[2] = {0, 0};

static void barricade_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_knockdown_standup_ms[player_index] = 0;
    }
}

static void barricade_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->target_bot_id || strstr(ctx->target_bot_id, "barricade") == NULL) return;
    if (!ctx->is_blocked && (ctx->is_heavy || (ctx->special_index > 0 && ctx->is_last_hit))) {
        s_knockdown_standup_ms[ctx->target_player_index] = skill_now_ms() + 900;
    }
}

static void barricade_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_knockdown_standup_ms[p] > 0 && now_ms >= s_knockdown_standup_ms[p]) {
            s_knockdown_standup_ms[p] = 0;
            const char* bid = skill_get_bot_id(p);
            if (!bid || strstr(bid, "barricade") == NULL) continue;

            if (skill_random_float() < 0.85f) {
                skill_apply_buff_dur(p, "barricade_knockdown_evade_melee", 3.0f);
            }
            if (skill_random_float() < 0.85f) {
                skill_apply_buff_dur(p, "barricade_knockdown_evade_ranged", 3.0f);
            }
            if (skill_random_float() < 0.40f) {
                skill_apply_buff_dur(p, "barricade_knockdown_crit_rate", 7.5f);
            }
            skill_log("BARRICADE: P%d knockdown standup triggered evade/crit buffs", p);
        }
    }
}

static int barricade_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade || !ctx->bot_id || strstr(ctx->bot_id, "barricade") == NULL) return 0;
    int p = ctx->player_index;
    if (!ctx->is_ranged && skill_has_buff(p, "barricade_knockdown_evade_melee")) {
        if (skill_random_float() < 0.85f) {
            *out_evade = 1;
            return 1;
        }
    } else if (ctx->is_ranged && skill_has_buff(p, "barricade_knockdown_evade_ranged")) {
        if (skill_random_float() < 0.85f) {
            *out_evade = 1;
            return 1;
        }
    }
    return 0;
}

BotSkillModule g_module_barricade = {
    .bot_prefix         = "barricade",
    .display_name_zh    = "路障",
    .on_hit_connected   = barricade_on_hit_connected,
    .on_evade_check     = barricade_on_evade_check,
    .on_simulation_tick = barricade_on_simulation_tick,
    .on_fight_reset     = barricade_on_fight_reset,
};
