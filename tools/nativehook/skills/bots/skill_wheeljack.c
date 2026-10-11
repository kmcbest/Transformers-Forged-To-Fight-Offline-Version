#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 千斤顶 (Wheeljack) 技能模块
// - SP 最终击判定: Shock, Power Leak, Stun 必须在收招最终击触发
// - Power Leak 施加后持续流失能量

static int wheeljack_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    if (strstr(ctx->modifier_id, "wheeljack_") != NULL) {
        if (strstr(ctx->modifier_id, "_shock") != NULL ||
            strstr(ctx->modifier_id, "_leak") != NULL ||
            strstr(ctx->modifier_id, "_stun") != NULL) {
            if (!ctx->current_hit_is_last) {
                skill_log("WHEELJACK_FINAL_HIT_GATE: suppressed %s (not final hit, flags=0x%x)", ctx->modifier_id, ctx->last_hit_flags);
                ctx->allow_application = false;
            } else {
                skill_log("WHEELJACK_FINAL_HIT_GATE: permitted %s on FINAL HIT (flags=0x%x)", ctx->modifier_id, ctx->last_hit_flags);
                ctx->allow_application = true;
            }
            return 1;
        }
    }

    return 0;
}

static void wheeljack_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return;

    if (strstr(ctx->modifier_id, "wheeljack_") != NULL && strstr(ctx->modifier_id, "_leak") != NULL) {
        skill_set_power_leak(1, 3000, 0.0022f);
        skill_log("POWER_LEAK_ACTIVATED: Wheeljack leak active for 3.0s on enemy");
    }
}

static void wheeljack_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_wheeljack = {
    .bot_prefix = "wheeljack",
    .on_hit_connected = NULL,
    .on_buff_gated = wheeljack_on_buff_gated,
    .on_buff_applied = wheeljack_on_buff_applied,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_fight_reset = wheeljack_on_fight_reset
};
