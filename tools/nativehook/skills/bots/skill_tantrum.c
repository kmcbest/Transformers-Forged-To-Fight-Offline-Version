#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 野牛 (Tantrum) 技能模块
// Bot ID: tantrum_gs_kabam
// ===========================================================================
// 1. [3438] 被动：防御蓄力与不可阻挡
//    进入防御状态 1.5 秒后，获得 4.5 秒不可阻挡增益 (灰色倒计时 1.5s 后变黄色不可阻挡)。
//    若在 1.5 秒内被打断 (如重击击倒) 或主动松开防御，则不会进入不可阻挡状态，灰色图标消失。
// 2. [3450] 被动：前冲近战增益
//    前冲时获得 1 层近战增益 (+24% 近战伤害，最多 10 层)。
//    若后闪且身上没有不可阻挡状态，则失去所有近战增益。
// ===========================================================================

static uint64_t s_tantrum_block_start_ms[2] = {0, 0};
static int      s_tantrum_charge_active[2]  = {0, 0};

static void tantrum_on_block_state(int p, int entered) {
    if (p < 0 || p >= 2) return;
    uint64_t now_ms = skill_now_ms();

    if (entered) {
        // 进入防御姿态: 如果当前身上已有不可阻挡，则不重复蓄力
        if (skill_is_unstoppable(p)) {
            skill_log("TANTRUM: P%d entered block while already unstoppable, skipping charge", p);
            return;
        }
        s_tantrum_block_start_ms[p] = now_ms;
        s_tantrum_charge_active[p] = 1;
        skill_apply_buff(p, "tantrum_block_charge");
        skill_log("TANTRUM: P%d entered block stance, armed 1.5s Unstoppable charge & applied gray icon", p);
    } else {
        // 退出防御姿态: 若正在蓄力且未满 1.5s，则打断蓄力并移除灰色图标
        if (s_tantrum_charge_active[p]) {
            s_tantrum_charge_active[p] = 0;
            s_tantrum_block_start_ms[p] = 0;
            skill_consume_buff(p, "tantrum_block_charge", 1);
            skill_log("TANTRUM: P%d released block before 1.5s, cancelled Unstoppable charge", p);
        }
    }
}

static void tantrum_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_tantrum_charge_active[p] && s_tantrum_block_start_ms[p] > 0) {
            uint64_t elapsed = now_ms - s_tantrum_block_start_ms[p];
            if (elapsed >= 1500) {
                // 坚守防御满 1.5 秒！激活不可阻挡
                s_tantrum_charge_active[p] = 0;
                s_tantrum_block_start_ms[p] = 0;

                // 移除灰色蓄力图标
                skill_consume_buff(p, "tantrum_block_charge", 1);

                // 激活 4.5 秒不可阻挡状态
                skill_set_unstoppable(p, 4500);

                // 主动施加黄色不可阻挡 Buff (弹出呼出与 HUD 图标)
                skill_apply_buff(p, "tantrum_block_unstoppable");

                skill_overlay("[%s] 坚守防御 1.5s！进入不可阻挡状态 (4.5s)",
                              p == 0 ? "野牛" : "敌方野牛");
                skill_log("TANTRUM: Block held for 1.5s on P%d! Activated 4.5s Unstoppable", p);
            }
        }
    }
}

static void tantrum_on_hitreact_enter(int p) {
    if (p < 0 || p >= 2) return;
    // 被受击打断 (如被重击击倒或破防受击)
    if (s_tantrum_charge_active[p]) {
        s_tantrum_charge_active[p] = 0;
        s_tantrum_block_start_ms[p] = 0;
        skill_consume_buff(p, "tantrum_block_charge", 1);
        skill_log("TANTRUM: P%d block stance interrupted by hitreact, cancelled Unstoppable charge", p);
    }
}

static void tantrum_on_dodge_enter(int p) {
    if (p < 0 || p >= 2) return;

    // 1. 若正在防御蓄力中后闪，取消蓄力
    if (s_tantrum_charge_active[p]) {
        s_tantrum_charge_active[p] = 0;
        s_tantrum_block_start_ms[p] = 0;
        skill_consume_buff(p, "tantrum_block_charge", 1);
    }

    // 2. [3450] 若野牛后闪且身上没有不可阻挡状态，则失去所有近战增益
    if (!skill_is_unstoppable(p)) {
        skill_consume_buff(p, "tantrum_dash_melee_buff", 10);
        skill_log("TANTRUM: P%d dodged while NOT unstoppable, removed all dash melee buffs", p);
    }
}

static int tantrum_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id) return 0;

    // 1. 防御蓄力灰色图标门禁: 若当前身上已有不可阻挡，阻止生成灰色蓄力
    if (strstr(ctx->modifier_id, "tantrum_block_charge") != NULL) {
        int tp = ctx->target_player_index;
        if (skill_is_unstoppable(tp)) {
            skill_log("TANTRUM: Suppressed tantrum_block_charge on P%d because already unstoppable", tp);
            ctx->allow_application = false;
            return 1;
        }
        ctx->allow_application = true;
        return 1;
    }

    return 0;
}

static void tantrum_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_tantrum_block_start_ms[player_index] = 0;
        s_tantrum_charge_active[player_index]  = 0;
    }
}

BotSkillModule g_module_tantrum = {
    .bot_prefix          = "tantrum",
    .on_hit_connected    = NULL,
    .on_buff_gated       = tantrum_on_buff_gated,
    .on_buff_applied     = NULL,
    .on_evade_check      = NULL,
    .on_test_roll        = NULL,
    .on_power_gain_rate  = NULL,
    .on_reflect_proj     = NULL,
    .on_fight_reset      = tantrum_on_fight_reset,
    .on_simulation_tick  = tantrum_on_simulation_tick,
    .on_block_state      = tantrum_on_block_state,
    .on_dodge_enter      = tantrum_on_dodge_enter,
    .on_hitreact_enter   = tantrum_on_hitreact_enter,
};
