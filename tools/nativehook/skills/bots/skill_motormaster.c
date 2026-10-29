#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 汽车大师 (Motormaster) 技能模块
// Bot ID: motormaster_gs_voyager2015
// ===========================================================================
// 1. [被动 - 前冲 / Dashing]:
//    - 严格限定：从远距离发起前冲攻击（进入原生 PlayerDashState），发起到结束的过程获得不可阻挡；
//    - 霸体时间不能超时（硬上限 600ms），一旦前冲命中、被格挡或退出前冲攻击状态，霸体立即归零清空；
//    - 贴脸近战出招、原地轻重击绝不给霸体。
// 2. [特殊技 2 - 大师级工艺 / A Master Craft]:
//    - SP2 (0x202 / 320) 发动时获得 4.0 秒不可阻挡霸体；
//    - 严格禁止 SP1 (0x201 / 16)、SP3 (0x203 / 64) 以及其他任何行为触发霸体。
// ===========================================================================

static uint64_t s_last_dash_ms[2] = {0, 0};
static uint64_t s_last_sp2_ms[2] = {0, 0};

static void motormaster_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "motormaster") == NULL) return;

    uint64_t now_ms = skill_now_ms();

    // 汽车大师前冲霸体：严格限定从中远距离发起前冲攻击 (dist >= 10.0f, 非近战范围, 非连招中) 时获得，上限 600ms；
    // 贴脸近战出招、原地连招 (M1/M2) 绝不给霸体。
    if (action_type == 2) {
        if (!skill_is_in_combo(player_index) && !skill_is_in_melee_range(player_index)) {
            float dist = skill_get_opponent_distance(player_index);
            if (dist >= 10.0f) {
                if (s_last_dash_ms[player_index] == 0 || now_ms - s_last_dash_ms[player_index] >= 800) {
                    s_last_dash_ms[player_index] = now_ms;
                    skill_set_motormaster_dash_unstoppable(player_index, 600);
                    skill_apply_buff_dur(player_index, "motormaster_dash_unstoppable", 0.6f);
                    skill_log("MOTORMASTER: P%d remote dash (dist=%.2f >= 10.0m) -> granted 600ms dash unstoppable", player_index, dist);
                }
            } else {
                skill_log("MOTORMASTER: P%d rejected dash unstoppable: dist=%.2f < 10.0m", player_index, dist);
            }
        } else {
            skill_log("MOTORMASTER: P%d rejected dash unstoppable: in combo or melee range", player_index);
        }
    } else if (action_type == 320 || action_type == 0x202) {
        // SP2 (特殊技 2) 释放时获得 4.0 秒真正定时的不可阻挡霸体 (严格限定 320 / 0x202，绝不包含 Action.Dash 32 与 SP1/SP3)
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
        skill_clear_motormaster_dash_unstoppable(player_index);
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
