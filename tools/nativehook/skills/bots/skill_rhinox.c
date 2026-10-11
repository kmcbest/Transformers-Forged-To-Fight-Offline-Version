#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 犀牛 (Rhinox) 技能模块
// - SP1 驱散敌人 Buff 后触发流血 (rhinox_sp1_nullify_bleed)

static int rhinox_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    if (strstr(ctx->modifier_id, "rhinox_sp1_nullify_bleed") != NULL) {
        int nullified = skill_get_p1_buffs_nullified();
        if (nullified <= 0) {
            skill_log("RHINOX_NULLIFY_GATE: suppressed bleed because 0 buffs were nullified from P1");
            ctx->allow_application = false;
        } else {
            skill_log("RHINOX_NULLIFY_GATE: permitted bleed because %d buff(s) nullified from P1", nullified);
            ctx->allow_application = true;
        }
        return 1; // 已处理
    }

    return 0;
}

static void rhinox_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_rhinox = {
    .bot_prefix = "rhinox",
    .on_hit_connected = NULL,
    .on_buff_gated = rhinox_on_buff_gated,
    .on_buff_applied = NULL,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_fight_reset = rhinox_on_fight_reset
};
