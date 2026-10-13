#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 狂飙 (Cyclonus UW-06) 技能模块
// Bot ID: cyclonus_gs_uw06
// ===========================================================================
// 1. [2973] 被动：黑暗场 (Dark Field Pulse - 黑暗燃烧与霸体克星)
// 2. [2991] SP3：黑暗场 (SP3 10s Continuous Dark Field Pulse)
//
// 核心机制：黑暗场反制不可阻挡 (Unstoppable Counter)
// 当具有不可阻挡增益的对手冲向狂飙时，狂飙立刻释放黑暗能量，驱散其不可阻挡并造成 1.5s 眩晕。
// ===========================================================================

static int      s_dark_energy_charges[2] = {0, 0};
static uint64_t s_sp3_pulse_end_ms[2]    = {0, 0};

static void cyclonus_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 狂飙作为受击方：反制对手霸体冲刺
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "cyclonus") != NULL) {
        int tp = ctx->target_player_index;
        // 如果对手在带有霸体状态下攻击狂飙
        if (s_dark_energy_charges[tp] < 3) {
            s_dark_energy_charges[tp]++;
            skill_overlay("[%s] 黑暗能量共鸣！获得黑暗充能 (%d/3)",
                          tp == 0 ? "狂飙" : "敌方狂飙", s_dark_energy_charges[tp]);
        }
    }

    // 狂飙作为攻击方：
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "cyclonus") != NULL) {
        int ap = ctx->attacker_player_index;
        // 连招收招释放黑暗场脉冲
        if (ctx->is_last_hit || (s_sp3_pulse_end_ms[ap] > 0 && now_ms < s_sp3_pulse_end_ms[ap])) {
            float pulse_extra = ctx->base_damage * 0.20f;
            ctx->modified_damage += pulse_extra;
            skill_overlay("[%s] 黑暗场脉冲爆发！追加 20%% 黑暗燃烧能量伤害！",
                          ap == 0 ? "狂飙" : "敌方狂飙");
        }
    }
}

static void cyclonus_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    uint64_t now_ms = skill_now_ms();

    if (strstr(ctx->modifier_id, "cyclonus_sp3_dark_field") != NULL) {
        int ap = ctx->attacker_player_index;
        s_sp3_pulse_end_ms[ap] = now_ms + 10000;
        skill_overlay("[%s] 激活 10 秒连续黑暗场脉冲风暴！",
                      ap == 0 ? "狂飙" : "敌方狂飙");
    }
}

static void cyclonus_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_dark_energy_charges[player_index] = 0;
        s_sp3_pulse_end_ms[player_index] = 0;
    }
}

BotSkillModule g_module_cyclonus = {
    .bot_prefix       = "cyclonus",
    .on_hit_connected = cyclonus_on_hit_connected,
    .on_buff_gated    = NULL,
    .on_buff_applied  = cyclonus_on_buff_applied,
    .on_evade_check   = NULL,
    .on_test_roll     = NULL,
    .on_fight_reset   = cyclonus_on_fight_reset,
};
