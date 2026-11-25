#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static int s_hotlink_unstop_used[2] = {0, 0};

static void hotlink_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_hotlink_unstop_used[player_index] = 0;
    }
}

static void hotlink_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "hotlink") == NULL) continue;
        float hp_r = skill_get_hp_ratio(p);
        if (!s_hotlink_unstop_used[p] && hp_r > 0.0f && hp_r <= 0.50f) {
            s_hotlink_unstop_used[p] = 1;
            skill_set_unstoppable(p, 6000);
            skill_apply_buff_dur(p, "hotlink_sig_unstoppable", 6.0f);
            skill_log("HOTLINK: P%d HP <= 50%% -> gained Unstoppable (6.0s)", p);
        }
    }
}

static void hotlink_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2 || entered != 0 || sp_level != 1) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "hotlink") == NULL) return;
    skill_apply_buff_dur(player_index, "hotlink_sp1_melee_buff", 6.0f);
}

static void hotlink_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "hotlink") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    if (!ctx->is_ranged && ctx->special_index == 0 && skill_is_burning(tp)) {
        ctx->modified_damage *= 1.25f;
        skill_apply_buff_dur(ap, "hotlink_burn_melee_boost", 4.0f);
        skill_apply_buff_dur(ap, "hotlink_sig_melee_stack", 5.0f);
    }
}

BotSkillModule g_module_hotlink = {
    .bot_prefix         = "hotlink",
    .display_name_zh    = "热链",
    .on_hit_connected   = hotlink_on_hit_connected,
    .on_simulation_tick = hotlink_on_simulation_tick,
    .on_special_state   = hotlink_on_special_state,
    .on_fight_reset     = hotlink_on_fight_reset,
};
