#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 汽车大师 (Motormaster) 技能模块
// Bot ID: motormaster_gs_voyager2015
// ===========================================================================
// 1. [被动 - 前冲 / Dashing]:
//    - 仅限中远距离冲锋 (dist >= 20.0米，远超近战缓冲区 MeleeRangeBuffer=16.0) 激活 550ms 冲刺霸体
//    - 贴脸近战出招 (dist < 20.0米) 与倒地起身贴脸出招绝不给霸体，通过 on_buff_gated 彻底拦截 C# 状态机触发
//    - 冲刺一旦命中或被格挡，立即清空霸体窗口，绝不溢出到后续普通攻击
// 2. [特殊技 2 - 大师级工艺 / A Master Craft]:
//    - SP2 (32 / 320 / 0x202) 释放时获得 4.0 秒真正定时的不可阻挡霸体
//    - 严禁对 SP1 (16 / 0x201) 触发霸体
// ===========================================================================

static uint64_t s_last_dash_ms[2] = {0, 0};
static uint64_t s_last_sp2_ms[2] = {0, 0};

static int motormaster_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id) return 0;
    // 关键门禁：前冲霸体必须仅限中远距离冲锋 (dist >= 20.0米)；
    // 贴脸近战出招、连续近战平A、以及倒地起身贴脸滑动，底层一律拦截，严禁施加 buff 与弹窗提示！
    if (strcmp(ctx->modifier_id, "motormaster_dash_unstoppable") == 0) {
        float dist = skill_get_opponent_distance(ctx->target_player_index);
        if (dist < 20.0f) {
            ctx->allow_application = false;
            skill_log("MOTORMASTER: Gated motormaster_dash_unstoppable at close range (dist=%.2f < 20.0m)", dist);
            return 1;
        }
        ctx->allow_application = true;
        return 1;
    }
    return 0;
}

static void motormaster_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "motormaster") == NULL) return;

    uint64_t now_ms = skill_now_ms();

    if (action_type == 2) {
        // 关键门禁：前冲霸体仅限中远距离冲锋 (dist >= 20.0米) 激活；贴脸近战出招 (dist < 20.0米) 绝不给霸体！
        float dist = skill_get_opponent_distance(player_index);
        if (dist >= 20.0f) {
            if (s_last_dash_ms[player_index] == 0 || now_ms - s_last_dash_ms[player_index] >= 800) {
                s_last_dash_ms[player_index] = now_ms;
                // 远距离冲锋霸体窗口 550ms，足以为其提供突进全场的霸体护甲 (命中或格挡时由 hook_186 立即清空)
                skill_set_motormaster_dash_unstoppable(player_index, 550);
                skill_apply_buff_dur(player_index, "motormaster_dash_unstoppable", 0.55f);
                skill_log("MOTORMASTER: P%d dash at remote distance %.2f >= 20.0m -> granted 550ms charge armor", player_index, dist);
            }
        } else {
            skill_log("MOTORMASTER: P%d dash at close distance %.2f < 20.0m -> NO unstoppable", player_index, dist);
        }
    } else if (action_type == 32 || action_type == 320 || action_type == 0x202) {
        // SP2 (特殊技 2) 释放时获得 4.0 秒真正定时的不可阻挡霸体 (注意：严格限定 32/320/0x202，绝不包含 SP1 的 16/0x201)
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
    .on_buff_gated = motormaster_on_buff_gated,
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
