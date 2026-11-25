#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 搅拌者 (Mixmaster ROTF) 技能模块
// 迁移自 hook.c & 补齐 SP1/SP3 末击与减益暴击判断

static int target_has_any_debuff(int tp) {
    return skill_has_buff(tp, "acid") || skill_has_buff(tp, "burn") ||
           skill_has_buff(tp, "bleed") || skill_has_buff(tp, "shock") ||
           skill_has_buff(tp, "armor_break") || skill_has_buff(tp, "stun");
}

static void mixmaster_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "mixmaster") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    if (target_has_any_debuff(tp) && !skill_has_buff(ap, "mixmaster_debuff_crit_rate")) {
        skill_apply_buff_dur(ap, "mixmaster_debuff_crit_rate", 4.0f);
    }
}

static int mixmaster_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strstr(ctx->modifier_id, "mixmaster_s2_burn") != NULL) {
        if (ctx->last_hit_index == 0 && !ctx->current_hit_is_last) {
            skill_log("MIXMASTER_GATE: hit 0 is punch, skip burn roll");
            *out_res = 0;
            return 1;
        }
    }

    if (strstr(ctx->modifier_id, "mixmaster_sp1_acid") != NULL ||
        strstr(ctx->modifier_id, "mixmaster_sp3_acid") != NULL ||
        strstr(ctx->modifier_id, "mixmaster_consume_") != NULL) {
        if (!ctx->current_hit_is_last) {
            *out_res = 0;
            return 1;
        }
    }

    return 0;
}

BotSkillModule g_module_mixmaster = {
    .bot_prefix       = "mixmaster",
    .display_name_zh  = "搅拌者",
    .on_hit_connected = mixmaster_on_hit_connected,
    .on_test_roll     = mixmaster_on_test_roll,
};
