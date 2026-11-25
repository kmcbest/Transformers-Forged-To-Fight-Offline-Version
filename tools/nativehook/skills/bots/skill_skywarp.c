#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void skywarp_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "skywarp") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (ctx->special_index == 2 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "skywarp_sp2_repair_block", 12.0f);
    } else if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_add_mana(tp, -1.50f);
        skill_add_mana(ap, 1.50f);
        skill_apply_buff_dur(tp, "skywarp_sp3_drain", 0.5f);
        skill_apply_buff_dur(ap, "skywarp_sp3_gain", 0.5f);
        skill_apply_buff(ap, "skywarp_sp3_power_flow");
        skill_log("SKYWARP: SP3 lastHit power steal + power flow on P%d", ap);
    }
}

BotSkillModule g_module_skywarp = {
    .bot_prefix       = "skywarp",
    .display_name_zh  = "闹翻天",
    .on_hit_connected = skywarp_on_hit_connected,
};
