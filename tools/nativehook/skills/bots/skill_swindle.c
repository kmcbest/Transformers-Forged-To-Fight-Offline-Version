#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void swindle_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "swindle") == NULL) return;
    int ap = ctx->attacker_player_index;
    if (ctx->special_index == 2 && ctx->is_last_hit) {
        skill_apply_buff_dur(ap, "swindle_sp2_reroll_upgrades", 0.5f);
    } else if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_apply_buff_dur(ap, "swindle_sp3_align_upgrades", 0.5f);
        skill_heal(ap, skill_get_max_hp(ap) * 0.10f);
    }
}

BotSkillModule g_module_swindle = {
    .bot_prefix       = "swindle",
    .display_name_zh  = "诈骗",
    .on_hit_connected = swindle_on_hit_connected,
};
