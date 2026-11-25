#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// G1 擎天柱 (Optimus Prime G1) 技能模块
// 迁移自 hook.c: SP1 仅后两击破甲、SP3 仅末击破甲

static int optimus_g1_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strstr(ctx->modifier_id, "optimus_sp1_armor_break") != NULL) {
        if (ctx->last_hit_index == 0) {
            skill_log("OPTIMUS_SP1_GATE: hit 0 is punch, skip armor break roll");
            *out_res = 0;
            return 1;
        }
    }

    if (strstr(ctx->modifier_id, "optimus_sp3_armor_break") != NULL) {
        if (!ctx->current_hit_is_last) {
            skill_log("OPTIMUS_SP3_GATE: non-last hit, skip armor break roll");
            *out_res = 0;
            return 1;
        }
    }

    if (strstr(ctx->modifier_id, "optimus_sig_armor_break_bleed") != NULL) {
        if (!skill_has_buff(ctx->target_player_index, "armor_break")) {
            *out_res = 0;
            return 1;
        }
    }

    return 0;
}

BotSkillModule g_module_optimus_g1 = {
    .bot_prefix      = "optimus",
    .display_name_zh = "擎天柱",
    .on_test_roll    = optimus_g1_on_test_roll,
};
