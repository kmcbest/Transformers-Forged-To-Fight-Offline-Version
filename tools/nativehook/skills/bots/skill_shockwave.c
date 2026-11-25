#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void shockwave_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "shockwave") == NULL) return;
    int tp = ctx->target_player_index;
    if (ctx->special_index == 1 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "shockwave_sp1_shock", 4.0f);
    } else if (ctx->special_index == 2 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "shockwave_sp2_repair_block", 6.5f);
    } else if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "shockwave_sp3_shock", 4.0f);
        skill_apply_buff_dur(tp, "shockwave_sp3_repair_block", 11.0f);
    }
}

BotSkillModule g_module_shockwave = {
    .bot_prefix       = "shockwave",
    .display_name_zh  = "震荡波",
    .on_hit_connected = shockwave_on_hit_connected,
};
