#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 暗天陨 / 黑暗擎天柱 (Nemesis Prime Voyager 2015) 技能模块
// Bot ID: nemesisprime_gs_voyager2015
// ===========================================================================
// 1. [3209] 被动：黑暗能量 (Dark Energy Charges)
//    50~100% 血量每 10s 1层，15~50% 每 7s 1层，<15% 每 5s 1层，最多 10 层。
//    开局紫色 (#D204F6) 倒计时图标 (\uE407)，走完获得紫色 (\uE90A) 层数图标，满 10 层消失，少于 10 层恢复。
// 2. [3218] 被动：重击驱散 (Heavy Dispel) - 每层黑暗能量重击伤害 +5%
// 3. [3221] 觉醒：赝品领导模块 (Fake Matrix Lifesteal - 特技伤害 25% 转化为生命)
// 4. [3224] SP3：不可防御 (SP3 Unblockable 7s + 0.5s/层，消耗全部黑暗能量)
// ===========================================================================

static int      s_nemesis_active[2]             = {0, 0};
static int      s_nemesis_dark_stacks[2]        = {0, 0};
static uint64_t s_last_dark_charge_ms[2]        = {0, 0};
static uint64_t s_current_dark_interval_ms[2]   = {10000, 10000};

static float get_nemesis_cd_seconds(int p, uint64_t* out_interval_ms) {
    float hp_ratio = skill_get_hp_ratio(p);
    if (hp_ratio < 0.15f) {
        if (out_interval_ms) *out_interval_ms = 5000;
        return 5.0f;
    } else if (hp_ratio < 0.50f) {
        if (out_interval_ms) *out_interval_ms = 7000;
        return 7.0f;
    } else {
        if (out_interval_ms) *out_interval_ms = 10000;
        return 10.0f;
    }
}

static void nemesis_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_nemesis_active[p] && s_nemesis_dark_stacks[p] < 10 && s_last_dark_charge_ms[p] > 0) {
            if (now_ms - s_last_dark_charge_ms[p] >= s_current_dark_interval_ms[p]) {
                s_nemesis_dark_stacks[p]++;
                skill_consume_buff(p, "nemesisprime_dark_cd", 1);
                skill_apply_buff_dur(p, "nemesisprime_dark_energy", -1.0f);
                skill_overlay("[%s] 黑暗能量充能 (%d/10)",
                              p == 0 ? "暗天陨" : "敌方暗天陨", s_nemesis_dark_stacks[p]);
                skill_log("NEMESIS: P%d gained Dark Energy stack %d/10", p, s_nemesis_dark_stacks[p]);

                if (s_nemesis_dark_stacks[p] < 10) {
                    uint64_t next_ms = 10000;
                    float dur = get_nemesis_cd_seconds(p, &next_ms);
                    s_last_dark_charge_ms[p] = now_ms;
                    s_current_dark_interval_ms[p] = next_ms;
                    skill_apply_buff_dur(p, "nemesisprime_dark_cd", dur);
                } else {
                    s_last_dark_charge_ms[p] = 0;
                }
            }
        }
    }
}

static void nemesis_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 暗天陨作为攻击方 (Attacker):
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "nemesisprime") != NULL) {
        int ap = ctx->attacker_player_index;

        // 1. [3221] 觉醒：赝品领导模块 (已由客户端 onSpecialHit Heal_BuffEffect 原生驱动回血与跳绿字)
        if (ctx->special_index > 0) {
            float lifesteal_amount = ctx->modified_damage * 0.25f;
            if (lifesteal_amount > 0.0f) {
                skill_overlay("[%s] 赝品领导模块吸血！(+%.0f HP)",
                              ap == 0 ? "暗天陨" : "敌方暗天陨", lifesteal_amount);
                skill_log("NEMESIS: Fake Matrix lifesteal on P%d: +%.1f HP (25%% of %.1f)",
                          ap, lifesteal_amount, ctx->modified_damage);
            }
        }

        // 2. [3218] 重击命中增伤 (每层黑暗能量重击伤害 +5%)
        if (ctx->is_heavy && ctx->is_last_hit && s_nemesis_dark_stacks[ap] > 0) {
            float boost = 1.0f + (0.05f * s_nemesis_dark_stacks[ap]);
            ctx->modified_damage *= boost;
            skill_overlay("[%s] %d 层黑暗能量加持！重击增伤 %.0f%%！",
                          ap == 0 ? "暗天陨" : "敌方暗天陨",
                          s_nemesis_dark_stacks[ap], (boost - 1.0f) * 100.0f);
        }
    }
}

static void nemesis_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;

    int tp = ctx->target_player_index;
    if (strstr(ctx->modifier_id, "nemesisprime_dark_cd") != NULL) {
        s_nemesis_active[tp] = 1;
        if (s_last_dark_charge_ms[tp] == 0) {
            uint64_t next_ms = 10000;
            float dur = get_nemesis_cd_seconds(tp, &next_ms);
            s_last_dark_charge_ms[tp] = skill_now_ms();
            s_current_dark_interval_ms[tp] = next_ms;
            ctx->override_duration = dur;
            skill_log("NEMESIS: Initial Dark Energy CD (%.1fs) started on P%d", dur, tp);
        }
        return;
    }

    if (strstr(ctx->modifier_id, "nemesisprime_sp3_unblockable") != NULL) {
        int stacks = s_nemesis_dark_stacks[tp];
        ctx->override_duration = 7.0f + (0.5f * (float)stacks);
        if (stacks > 0) {
            skill_consume_buff(tp, "nemesisprime_dark_energy", 10);
            s_nemesis_dark_stacks[tp] = 0;
            uint64_t next_ms = 10000;
            float dur = get_nemesis_cd_seconds(tp, &next_ms);
            s_last_dark_charge_ms[tp] = skill_now_ms();
            s_current_dark_interval_ms[tp] = next_ms;
            skill_apply_buff_dur(tp, "nemesisprime_dark_cd", dur);
            skill_overlay("[%s] SP3消耗%d层黑暗能量！不可防御持续 %.1f 秒！重新开始充能！",
                          tp == 0 ? "暗天陨" : "敌方暗天陨", stacks, ctx->override_duration);
        }
    }
}

static void nemesis_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_nemesis_active[player_index]           = 0;
        s_nemesis_dark_stacks[player_index]      = 0;
        s_last_dark_charge_ms[player_index]      = 0;
        s_current_dark_interval_ms[player_index] = 10000;
    }
}

BotSkillModule g_module_nemesis = {
    .bot_prefix         = "nemesisprime",
    .on_hit_connected   = nemesis_on_hit_connected,
    .on_buff_gated      = NULL,
    .on_buff_applied    = nemesis_on_buff_applied,
    .on_evade_check     = NULL,
    .on_test_roll       = NULL,
    .on_fight_reset     = nemesis_on_fight_reset,
    .on_simulation_tick = nemesis_on_simulation_tick,
};
