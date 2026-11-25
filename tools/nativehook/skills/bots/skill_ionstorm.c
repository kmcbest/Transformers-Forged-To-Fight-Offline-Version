#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void ionstorm_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "ionstorm") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (ctx->is_heavy) {
        if (skill_has_buff(tp, "armor_up")) {
            skill_consume_buff(tp, "armor_up", 1);
            skill_apply_buff(tp, "ionstorm_heavy_nullify_armor");
        }
        if (skill_is_unstoppable(tp)) {
            skill_consume_buff(tp, "unstoppable", 99);
            skill_apply_buff(tp, "ionstorm_heavy_nullify_unstop");
        }
    }

    if (skill_has_buff(tp, "armor_break")) {
        ctx->modified_damage *= 1.25f;
        skill_apply_buff_dur(ap, "ionstorm_armor_broken_boost", 6.0f);
    }
}

BotSkillModule g_module_ionstorm = {
    .bot_prefix       = "ionstorm",
    .display_name_zh  = "离子风",
    .on_hit_connected = ionstorm_on_hit_connected,
};
