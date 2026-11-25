#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void soundwave_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "soundwave") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (ctx->special_index == 1 && ctx->is_last_hit) {
        if (skill_random_float() < 0.60f) {
            skill_apply_buff_dur(tp, "soundwave_sp1_stun", 1.5f);
            skill_stun_player(tp, 1.5f);
        }
        if (skill_random_float() < 0.85f) {
            skill_apply_buff_dur(tp, "soundwave_sp1_power_leak", 4.0f);
        }
    } else if (ctx->special_index == 2 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "soundwave_sp2_shock", 6.0f);
        skill_apply_buff_dur(ap, "soundwave_sp2_power_flow", 15.0f);
    } else if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "soundwave_sp3_shock", 6.0f);
        if (skill_random_float() < 0.60f) {
            skill_apply_buff_dur(tp, "soundwave_sp3_stun", 1.5f);
            skill_stun_player(tp, 1.5f);
        }
        if (skill_random_float() < 0.70f) {
            skill_apply_buff_dur(tp, "soundwave_sp3_power_lock", 8.0f);
        }
    }
}

BotSkillModule g_module_soundwave = {
    .bot_prefix       = "soundwave",
    .display_name_zh  = "声波",
    .on_hit_connected = soundwave_on_hit_connected,
};
