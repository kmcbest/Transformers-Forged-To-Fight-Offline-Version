#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void grindor_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->target_bot_id || strstr(ctx->target_bot_id, "grindor") == NULL) return;
    if (skill_random_float() < 0.11f) {
        skill_apply_buff_dur(ctx->attacker_player_index, "grindor_struck_crit_debuff", 6.0f);
    }
}

BotSkillModule g_module_grindor = {
    .bot_prefix       = "grindor",
    .display_name_zh  = "眩晕重机",
    .on_hit_connected = grindor_on_hit_connected,
};
