#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdio.h>

// ===========================================================================
// 千斤顶 (Wheeljack) 技能模块
// Bot ID: wheeljack_gs_mp20
// 职业: 科技系 (Tech) | 阵营: 汽车人 (Autobot)
// ===========================================================================
// 1. [特殊技 1/2/3 - 科技三合一]
//    - 60% 几率施加震击 (200% ATK, 6秒)
//    - 能量流失 (SP1: 50% 几率流失半格; SP2/SP3: 100% 几率流失整格，持续3秒)
//    - 10% 几率造成眩晕 (3秒)
// 2. [收招门禁] 减益必须在收招最终击 (LastHit) 触发
// ===========================================================================

static void wheeljack_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "wheeljack") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;
        int sp = ctx->special_index;

        if (sp >= 1 && sp <= 3 && ctx->is_last_hit) {
            char mod_shock[48], mod_leak[48], mod_stun[48];
            snprintf(mod_shock, sizeof(mod_shock), "wheeljack_sp%d_shock", sp);
            snprintf(mod_leak, sizeof(mod_leak), "wheeljack_sp%d_leak", sp);
            snprintf(mod_stun, sizeof(mod_stun), "wheeljack_sp%d_stun", sp);

            // 1. 60% 几率施加震击
            if (skill_random_float() < 0.60f) {
                skill_apply_buff_dur(tp, mod_shock, 6.0f);
                skill_apply_buff_dur(tp, "dmg_shock", 6.0f);
                skill_overlay("[%s] SP%d 震击发明！施加6秒震击！", ap == 0 ? "千斤顶" : "敌方千斤顶", sp);
                skill_log("WHEELJACK_SHOCK: P%d applied %s on P%d", ap, mod_shock, tp);
            }

            // 2. 能量流失 (Power Leak): SP1 50%, SP2/SP3 100%
            float leak_chance = (sp == 1) ? 0.50f : 1.0f;
            if (skill_random_float() < leak_chance) {
                skill_apply_buff_dur(tp, mod_leak, 3.0f);
                skill_apply_buff_dur(tp, "power_leak", 3.0f);
                skill_set_power_leak(tp, 3000, 0.0033f);
                skill_overlay("[%s] SP%d 能量流失！3秒内流失能量！", ap == 0 ? "千斤顶" : "敌方千斤顶", sp);
                skill_log("WHEELJACK_LEAK: P%d applied %s on P%d", ap, mod_leak, tp);
            }

            // 3. 10% 几率眩晕 (Stun)
            if (skill_random_float() < 0.10f) {
                skill_apply_buff_dur(tp, mod_stun, 3.0f);
                skill_stun_player(tp, 3.0f);
                skill_overlay("[%s] SP%d 科技震荡！眩晕对手3秒！", ap == 0 ? "千斤顶" : "敌方千斤顶", sp);
                skill_log("WHEELJACK_STUN: P%d stunned P%d for 3.0s", ap, tp);
            }
        }
    }
}

static int wheeljack_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return 0;

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
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return;

    if (strstr(ctx->modifier_id, "wheeljack_") != NULL && strstr(ctx->modifier_id, "_leak") != NULL) {
        skill_set_power_leak(ctx->target_player_index, 3000, 0.0033f);
        skill_log("POWER_LEAK_ACTIVATED: Wheeljack leak active for 3.0s on P%d", ctx->target_player_index);
    }
}

static void wheeljack_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_wheeljack = {
    .bot_prefix         = "wheeljack",
    .on_hit_connected   = wheeljack_on_hit_connected,
    .on_buff_gated       = wheeljack_on_buff_gated,
    .on_buff_applied     = wheeljack_on_buff_applied,
    .on_evade_check     = NULL,
    .on_simulation_tick = NULL,
    .on_fight_reset     = wheeljack_on_fight_reset
};
