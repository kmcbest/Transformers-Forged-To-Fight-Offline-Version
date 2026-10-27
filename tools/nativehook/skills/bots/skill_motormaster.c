#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 汽车大师 (Motormaster) 技能模块
// Bot ID: motormaster_gs_voyager2015
// ===========================================================================
// 1. [被动 - 前冲 / Dashing]:
//    前冲 (action=2) 时在 Dash 状态机中拥有不可阻挡霸体 (由 hook_194 判定 state=="Dash" 精确实现)
//    此处仅记录 buff 标记，绝不调用全局定时霸体，防止霸体时间溢出至近战 M1/L1
// 2. [特殊技 2 - 大师级工艺 / A Master Craft]:
//    SP2 (action=320/0x202) 释放时获得 4.0 秒真正定时的不可阻挡霸体 (motormaster_sp2_unstoppable)
// ===========================================================================

static uint64_t s_last_dash_ms[2] = {0, 0};
static uint64_t s_last_sp2_ms[2] = {0, 0};

static void motormaster_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "motormaster") == NULL) return;

    uint64_t now_ms = skill_now_ms();

    if (action_type == 2) {
        // 前冲触发 buff 记录 (冷却 800ms 防抖)
        // 关键防护：汽车大师前冲霸体属于仅限位移过程中的状态霸体，实际霸体由 hook_194 判定 state=="Dash" 精确提供；
        // 此处绝不调用 skill_set_unstoppable(700)，否则会给角色强加 700ms 计时器，溢出到随后的 M1/L1 近战攻击中，导致伪全程霸体！
        if (s_last_dash_ms[player_index] == 0 || now_ms - s_last_dash_ms[player_index] >= 800) {
            s_last_dash_ms[player_index] = now_ms;
            skill_apply_buff_dur(player_index, "motormaster_dash_unstoppable", 0.7f);
            skill_log("MOTORMASTER: P%d dash -> active (state-based unstoppable)", player_index);
        }
    } else if (action_type == 320 || action_type == 0x202 || action_type == 32) {
        // SP2 (特殊技 2) 释放时获得 4.0 秒真正定时的不可阻挡霸体
        if (s_last_sp2_ms[player_index] == 0 || now_ms - s_last_sp2_ms[player_index] >= 2000) {
            s_last_sp2_ms[player_index] = now_ms;
            skill_set_unstoppable(player_index, 4000);
            skill_apply_buff_dur(player_index, "motormaster_sp2_unstoppable", 4.0f);
            skill_overlay("[%s] 汽车大师SP2霸体激活！(4.0s)", player_index == 0 ? "我方" : "敌方");
            skill_log("MOTORMASTER: P%d SP2 -> gained unstoppable 4.0s", player_index);
        }
    }
}

static void motormaster_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_last_dash_ms[player_index] = 0;
        s_last_sp2_ms[player_index] = 0;
    }
}

BotSkillModule g_module_motormaster = {
    .bot_prefix = "motormaster",
    .on_hit_connected = NULL,
    .on_buff_gated = NULL,
    .on_buff_applied = NULL,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj = NULL,
    .on_fight_reset = motormaster_on_fight_reset,
    .on_simulation_tick = NULL,
    .on_block_state = NULL,
    .on_dodge_enter = NULL,
    .on_hitreact_enter = NULL,
    .on_attack_start = motormaster_on_attack_start
};
