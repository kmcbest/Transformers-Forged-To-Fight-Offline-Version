#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 阿尔茜 (Arcee) 技能模块
// - SP1 & SP3 踢击门禁: 踢击动作段不触发流血
// - SP1 绝技射击 (trick_shot): 命中后获得 6.5s 远程伤害+35%, 远程射速+40%

static int arcee_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    if (strstr(ctx->modifier_id, "arcee_") != NULL) {
        if (strstr(ctx->modifier_id, "sp1_") != NULL || strstr(ctx->modifier_id, "headshot_") != NULL) {
            if (ctx->current_special_index == 1 && ctx->last_hit_index == 0) {
                skill_log("ARCEE_SP1_KICK_GATE: suppressed %s on hit_index=%d (kick)", ctx->modifier_id, ctx->last_hit_index);
                ctx->allow_application = false;
                return 1;
            }
        }
        if (strstr(ctx->modifier_id, "sp3_") != NULL) {
            if (ctx->current_special_index == 3 && ctx->last_hit_index <= 1) {
                skill_log("ARCEE_SP3_KICK_GATE: suppressed %s on hit_index=%d (kick)", ctx->modifier_id, ctx->last_hit_index);
                ctx->allow_application = false;
                return 1;
            }
        }
    }

    return 0;
}

static void arcee_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return;

    if (strstr(ctx->modifier_id, "arcee_sp1_trick_shot") != NULL) {
        skill_set_ranged_boost(0, 6500, 0.35f, 0.40f);
        skill_log("RANGED_BOOST_ACTIVATED: Arcee SP1 (dmg=+35%%, spd=+40%%, dur=6.5s)");
    }
}

static void arcee_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_arcee = {
    .bot_prefix = "arcee",
    .on_hit_connected = NULL,
    .on_buff_gated = arcee_on_buff_gated,
    .on_buff_applied = arcee_on_buff_applied,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_fight_reset = arcee_on_fight_reset
};
