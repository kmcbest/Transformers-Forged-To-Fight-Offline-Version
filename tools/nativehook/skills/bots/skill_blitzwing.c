#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 闪电 (Blitzwing) 专属三变形态切换技能模块
// Bot ID: blitzwing_gs
// ===========================================================================
// 1. 开局默认进入【坦克形态】，显示白色 E902 图标。
//    在此形态下重击为威震天的坦克放炮 (move_heavy_megatron_gs_shoot)。
// 2. 按住防御满 1.0 秒 (1000ms)，触发三变变形，切换至【战机形态】。
//    图标切换为白色 E184 图标。
//    在此形态下重击变为喷气机战机冲撞 (move_heavy_ramjet_donut)。
// 3. 再次按住防御 1.0 秒可无缝切换回【坦克形态】。
// ===========================================================================

static int      s_blitzwing_active[2]         = {0, 0};
static int      s_blitzwing_mode[2]           = {0, 0}; // 0 = TANK (E902), 1 = JET (E184)
static uint64_t s_block_start_ms[2]           = {0, 0};
static int      s_switched_this_block[2]      = {0, 0};

int skill_blitzwing_get_mode(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        return s_blitzwing_mode[player_index];
    }
    return 0;
}

static void blitzwing_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = skill_get_bot_id(player_index);
    if (bot_id && strstr(bot_id, "blitzwing") != NULL) {
        s_blitzwing_active[player_index] = 1;
        s_blitzwing_mode[player_index] = 0; // 默认坦克形态
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;

        // 清除旧 Buff 并施加开局坦克形态 Buff (白色 E902 图标)
        skill_consume_buff(player_index, "blitzwing_jet_mode", 99);
        skill_consume_buff(player_index, "blitzwing_tank_mode", 99);
        skill_apply_buff_dur(player_index, "blitzwing_tank_mode", -1.0f);

        skill_overlay("[%s] 登场！默认【坦克形态】(E902)",
                      player_index == 0 ? "闪电" : "敌方闪电");
        skill_log("BLITZWING: P%d initialized in TANK MODE (E902)", player_index);
    } else {
        s_blitzwing_active[player_index] = 0;
        s_blitzwing_mode[player_index] = 0;
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;
    }
}

static void blitzwing_on_block_state(int player_index, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    if (!s_blitzwing_active[player_index]) return;

    if (entered) {
        s_block_start_ms[player_index] = skill_now_ms();
        s_switched_this_block[player_index] = 0;
        skill_log("BLITZWING: P%d started holding block at %lu ms",
                  player_index, (unsigned long)s_block_start_ms[player_index]);
    } else {
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;
    }
}

static void blitzwing_on_hitreact_enter(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;
    }
}

static void blitzwing_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (!s_blitzwing_active[p]) continue;

        // 持续按住防御 1.0 秒 (1000ms) 触发三变变形切换
        if (s_block_start_ms[p] > 0 && !s_switched_this_block[p]) {
            if (now_ms - s_block_start_ms[p] >= 1000) {
                s_switched_this_block[p] = 1;

                if (s_blitzwing_mode[p] == 0) {
                    // 坦克形态 -> 战机形态
                    s_blitzwing_mode[p] = 1;
                    skill_consume_buff(p, "blitzwing_tank_mode", 99);
                    skill_apply_buff_dur(p, "blitzwing_jet_mode", -1.0f);
                    skill_overlay("[%s] 变形！切换至【战机形态】(E184)！",
                                  p == 0 ? "闪电" : "敌方闪电");
                    skill_log("BLITZWING: P%d switched to JET MODE (E184)", p);
                } else {
                    // 战机形态 -> 坦克形态
                    s_blitzwing_mode[p] = 0;
                    skill_consume_buff(p, "blitzwing_jet_mode", 99);
                    skill_apply_buff_dur(p, "blitzwing_tank_mode", -1.0f);
                    skill_overlay("[%s] 变形！切换至【坦克形态】(E902)！",
                                  p == 0 ? "闪电" : "敌方闪电");
                    skill_log("BLITZWING: P%d switched to TANK MODE (E902)", p);
                }
            }
        }
    }
}

BotSkillModule g_module_blitzwing = {
    .bot_prefix = "blitzwing",
    .on_hit_connected = NULL,
    .on_buff_gated = NULL,
    .on_buff_applied = NULL,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj = NULL,
    .on_projectile_speed = NULL,
    .on_fight_reset = blitzwing_on_fight_reset,
    .on_simulation_tick = blitzwing_on_simulation_tick,
    .on_block_state = blitzwing_on_block_state,
    .on_dodge_enter = NULL,
    .on_opponent_block_state = NULL,
    .on_opponent_dodge_enter = NULL,
    .on_hitreact_enter = blitzwing_on_hitreact_enter,
    .on_attack_start = NULL
};
