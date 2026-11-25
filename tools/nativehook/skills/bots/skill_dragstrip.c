#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static int dragstrip_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    if (skill_has_buff(ctx->player_index, "dragstrip_sp2_anti_evade")) {
        *out_evade = 0;
        return 1;
    }
    return 0;
}

static void dragstrip_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "dragstrip") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 被动：对手流血层数 >= 3 时消耗流血并触发 4s 修复 5% HP
    if (skill_count_buffs(tp, "bleed") >= 3) {
        skill_consume_buff(tp, "bleed", 99);
        skill_apply_buff_dur(ap, "dragstrip_bleed_stack_heal", 4.0f);
        skill_apply_buff(tp, "dragstrip_bleed_stack_consume");
        skill_heal(ap, skill_get_max_hp(ap) * 0.05f);
    }

    if (ctx->special_index == 1 && ctx->is_last_hit) {
        skill_apply_buff_dur(ap, "dragstrip_sp1_crit_rate", 5.0f);
    } else if (ctx->special_index == 2 && ctx->is_last_hit) {
        skill_apply_buff_dur(ap, "dragstrip_sp2_crit_rate", 8.0f);
        skill_apply_buff_dur(tp, "dragstrip_sp2_anti_evade", 8.0f);
    }
}

BotSkillModule g_module_dragstrip = {
    .bot_prefix       = "dragstrip",
    .display_name_zh  = "抢劫",
    .on_hit_connected = dragstrip_on_hit_connected,
    .on_evade_check   = dragstrip_on_evade_check,
};
