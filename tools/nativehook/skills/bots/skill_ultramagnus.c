#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 通天晓 (Ultra Magnus) 技能模块
// 迁移自 hook.c: SP2/SP3 分段破甲与导弹燃烧门禁

static int ultramagnus_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    // SP2: 第一下槌击 (hit 0) 破甲，第二下 (最后一下) 导弹燃烧
    if (strstr(ctx->modifier_id, "ultramagnus_sp2_armor_break") != NULL) {
        if (ctx->last_hit_index != 0) {
            *out_res = 0;
            return 1;
        }
    }
    if (strstr(ctx->modifier_id, "ultramagnus_sp2_burn") != NULL) {
        if (!ctx->current_hit_is_last && ctx->last_hit_index == 0) {
            *out_res = 0;
            return 1;
        }
    }

    // SP3: 第一下槌击 (hit 0) 破甲，后面几下 (hit > 0) 导弹燃烧
    if (strstr(ctx->modifier_id, "ultramagnus_sp3_armor_break") != NULL) {
        if (ctx->last_hit_index != 0) {
            *out_res = 0;
            return 1;
        }
    }
    if (strstr(ctx->modifier_id, "ultramagnus_sp3_burn") != NULL) {
        if (ctx->last_hit_index == 0) {
            *out_res = 0;
            return 1;
        }
    }

    return 0;
}

BotSkillModule g_module_ultramagnus = {
    .bot_prefix      = "ultramagnus",
    .display_name_zh = "通天晓",
    .on_test_roll    = ultramagnus_on_test_roll,
};
