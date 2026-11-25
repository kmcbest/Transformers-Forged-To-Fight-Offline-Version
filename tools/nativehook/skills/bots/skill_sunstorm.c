#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static uint64_t s_sunstorm_last_tick_ms[2] = {0, 0};
static float    s_sunstorm_drained_ratio[2] = {0.0f, 0.0f};
static int      s_sunstorm_reactor_stacks[2] = {0, 0};

static void sunstorm_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_sunstorm_last_tick_ms[player_index] = 0;
        s_sunstorm_drained_ratio[player_index] = 0.0f;
        s_sunstorm_reactor_stacks[player_index] = 0;
    }
}

static void sunstorm_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "sunstorm") == NULL) continue;
        float hp_r = skill_get_hp_ratio(p);
        if (hp_r <= 0.40f) continue;

        if (s_sunstorm_last_tick_ms[p] == 0) {
            s_sunstorm_last_tick_ms[p] = now_ms;
            continue;
        }
        if (now_ms >= s_sunstorm_last_tick_ms[p] + 1000) {
            s_sunstorm_last_tick_ms[p] = now_ms;
            float max_hp = skill_get_max_hp(p);
            float drain = max_hp * 0.005f;
            if (drain > 0.0f) {
                skill_deal_damage(p, drain);
                s_sunstorm_drained_ratio[p] += 0.005f;
                int target_stacks = (int)(s_sunstorm_drained_ratio[p] / 0.10f);
                if (target_stacks > 4) target_stacks = 4;
                while (s_sunstorm_reactor_stacks[p] < target_stacks) {
                    s_sunstorm_reactor_stacks[p]++;
                    skill_apply_buff_dur(p, "sunstorm_sig_melee_gain", 30.0f);
                }
            }
        }
    }
}

static void sunstorm_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2 || entered != 0 || sp_level != 1) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "sunstorm") == NULL) return;
    skill_apply_buff_dur(player_index, "sunstorm_sp1_crit_buff", 4.0f);
}

static int sunstorm_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    (void)out_evade;
    if (!ctx) return 0;
    int ap = 1 - ctx->player_index;
    const char* atk_bid = skill_get_bot_id(ap);
    if (atk_bid && strstr(atk_bid, "sunstorm") != NULL && skill_is_burning(ctx->player_index)) {
        ctx->modified_chance -= 0.35f;
        if (ctx->modified_chance < 0.0f) ctx->modified_chance = 0.0f;
    }
    return 0;
}

static void sunstorm_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "sunstorm") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    if (skill_is_burning(tp)) {
        skill_apply_buff_dur(tp, "sunstorm_burn_anti_evade", 4.0f);
    }
    if (!ctx->is_ranged && s_sunstorm_reactor_stacks[ap] > 0) {
        ctx->modified_damage *= (1.0f + 0.15f * (float)s_sunstorm_reactor_stacks[ap]);
    }
}

BotSkillModule g_module_sunstorm = {
    .bot_prefix         = "sunstorm",
    .display_name_zh    = "太阳风",
    .on_hit_connected   = sunstorm_on_hit_connected,
    .on_evade_check     = sunstorm_on_evade_check,
    .on_special_state   = sunstorm_on_special_state,
    .on_simulation_tick = sunstorm_on_simulation_tick,
    .on_fight_reset     = sunstorm_on_fight_reset,
};
