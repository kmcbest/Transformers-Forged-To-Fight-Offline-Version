#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 汽车大师 (Motormaster) 技能模块
// Bot ID: motormaster_gs_voyager2015
// ===========================================================================
// 1. [被动 - 前冲 / Dashing]:
//    前冲 (action=2) 时获得 0.7 秒不可阻挡霸体 (motormaster_dash_unstoppable)
// 2. [特殊技 2 - 大师级工艺 / A Master Craft]:
//    SP2 (action=32) 释放时获得 4.0 秒不可阻挡霸体 (motormaster_sp2_unstoppable)
// ===========================================================================

static void motormaster_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "motormaster") == NULL) return;

    if (action_type == 2) {
        // 前冲获得 0.7 秒不可阻挡霸体
        skill_set_unstoppable(player_index, 700);
        skill_apply_buff_dur(player_index, "motormaster_dash_unstoppable", 0.7f);
        skill_overlay("[%s] 汽车大师前冲霸体激活！(0.7s)", player_index == 0 ? "我方" : "敌方");
        skill_log("MOTORMASTER: P%d dash -> gained unstoppable 0.7s", player_index);
    } else if (action_type == 32 || action_type == 320 || action_type == 0x202) {
        // SP2 获得 4.0 秒不可阻挡霸体
        skill_set_unstoppable(player_index, 4000);
        skill_apply_buff_dur(player_index, "motormaster_sp2_unstoppable", 4.0f);
        skill_overlay("[%s] 汽车大师SP2霸体激活！(4.0s)", player_index == 0 ? "我方" : "敌方");
        skill_log("MOTORMASTER: P%d SP2 -> gained unstoppable 4.0s", player_index);
    }
}

static void motormaster_on_fight_reset(int player_index) {
    (void)player_index;
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
