#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void acidstorm_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "acidstorm") != NULL) {
        if (!ctx->is_ranged && ctx->special_index == 0) {
            if (skill_random_float() < 0.25f) {
                skill_apply_buff_dur(ap, "acidstorm_splash_break", 5.0f);
                skill_log("ACIDSTORM: P%d splashed armor break onto P%d", tp, ap);
            }
        }
    }

    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "acidstorm") != NULL) {
        if (skill_is_burning(tp)) {
            ctx->modified_damage *= 1.20f;
            skill_apply_buff_dur(ap, "acidstorm_acid_atk_boost", 5.0f);
        }
    }
}

BotSkillModule g_module_acidstorm = {
    .bot_prefix       = "acidstorm",
    .display_name_zh  = "酸雨",
    .on_hit_connected = acidstorm_on_hit_connected,
};
