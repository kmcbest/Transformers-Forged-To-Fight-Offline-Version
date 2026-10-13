#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 暗天陨 / 黑暗擎天柱 (Nemesis Prime Voyager 2015) 技能模块
// Bot ID: nemesisprime_gs_voyager2015
// ===========================================================================
// 1. [3209] 被动：黑暗能量 (Dark Energy Charges)
// 2. [3218] 被动：重击驱散 (Heavy Dispel)
// 3. [3221] 觉醒：赝品领导模块 (Fake Matrix Lifesteal - 特技伤害 25% 转化为生命)
// 4. [3224] SP3：不可防御 (SP3 Unblockable 7s+)
// ===========================================================================

static int      s_nemesis_dark_stacks[2] = {0, 0};
static uint64_t s_last_dark_charge_ms[2] = {0, 0};

static void nemesis_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 暗天陨作为攻击方 (Attacker):
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "nemesisprime") != NULL) {
        int ap = ctx->attacker_player_index;

        // 1. [3209] 黑暗能量周期充能逻辑
        if (s_last_dark_charge_ms[ap] == 0) s_last_dark_charge_ms[ap] = now_ms;
        float hp_ratio = skill_get_hp_ratio(ap);
        uint64_t interval_ms = 10000;
        if (hp_ratio < 0.15f) {
            interval_ms = 5000;
        } else if (hp_ratio < 0.50f) {
            interval_ms = 7000;
        }

        if (now_ms - s_last_dark_charge_ms[ap] >= interval_ms && s_nemesis_dark_stacks[ap] < 10) {
            s_nemesis_dark_stacks[ap]++;
            s_last_dark_charge_ms[ap] = now_ms;
            skill_overlay("[%s] 黑暗能量充能 (%d/10)",
                          ap == 0 ? "暗天陨" : "敌方暗天陨", s_nemesis_dark_stacks[ap]);
        }

        // 2. [3221] 觉醒：赝品领导模块 (已由客户端 onSpecialHit Heal_BuffEffect 原生驱动回血与跳绿字)
        if (ctx->special_index > 0) {
            float lifesteal_amount = ctx->modified_damage * 0.25f;
            if (lifesteal_amount > 0.0f) {
                skill_overlay("[%s] 赝品领导模块吸血！(+%.0f HP)",
                              ap == 0 ? "暗天陨" : "敌方暗天陨", lifesteal_amount);
                skill_log("NEMESIS: Fake Matrix lifesteal on P%d: +%.1f HP (25%% of %.1f)",
                          ap, lifesteal_amount, ctx->modified_damage);
            }
        }

        // 3. [3218] 重击命中增伤并消耗黑暗能量
        if (ctx->is_last_hit && s_nemesis_dark_stacks[ap] > 0) {
            float boost = 1.0f + (0.05f * s_nemesis_dark_stacks[ap]);
            ctx->modified_damage *= boost;
            skill_overlay("[%s] 消耗 %d 层黑暗能量！重击增伤 %.0f%%！",
                          ap == 0 ? "暗天陨" : "敌方暗天陨",
                          s_nemesis_dark_stacks[ap], (boost - 1.0f) * 100.0f);
        }
    }
}

static void nemesis_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_nemesis_dark_stacks[player_index] = 0;
        s_last_dark_charge_ms[player_index] = 0;
    }
}

BotSkillModule g_module_nemesis = {
    .bot_prefix       = "nemesisprime",
    .on_hit_connected = nemesis_on_hit_connected,
    .on_buff_gated    = NULL,
    .on_buff_applied  = NULL,
    .on_evade_check   = NULL,
    .on_test_roll     = NULL,
    .on_fight_reset   = nemesis_on_fight_reset,
};
