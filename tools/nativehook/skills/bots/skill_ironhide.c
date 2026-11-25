#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 铁皮 (Ironhide) 技能模块
// 迁移自 hook.c: SP1 导弹末击门禁、初次燃烧与叠层燃烧互斥逻辑

static int s_ironhide_burned_this_hit = 0;
static uint64_t s_ironhide_gs_sp2_armor_ms[2] = {0, 0};

static void ironhide_on_hit_begin(void) {
    s_ironhide_burned_this_hit = 0;
}

static void ironhide_on_fight_reset(int player_index) {
    s_ironhide_burned_this_hit = 0;
    if (player_index >= 0 && player_index < 2) {
        s_ironhide_gs_sp2_armor_ms[player_index] = 0;
    }
}

static int ironhide_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    // a) SP1 仅最后一击算导弹攻击 (前置近战拳脚不触发燃烧与导弹暴击)
    if (strstr(ctx->modifier_id, "ironhide_missile_") != NULL) {
        if (ctx->current_special_index == 1 && !ctx->current_hit_is_last) {
            skill_log("IRONHIDE_GATE: SP1 non-last hit, skip missile roll: %s", ctx->modifier_id);
            *out_res = 0;
            return 1;
        }
    }

    // b) 初次燃烧与叠层燃烧互斥逻辑:
    // 若目标在本次打击前未燃烧，施加 80% 初次燃烧；若已在燃烧，施加 30% 叠层燃烧。
    if (strstr(ctx->modifier_id, "ironhide_missile_burn") != NULL) {
        int target_already_burning = skill_is_burning(ctx->target_player_index);
        if (strstr(ctx->modifier_id, "ironhide_missile_burn_stack") != NULL) {
            if (!target_already_burning || s_ironhide_burned_this_hit) {
                skill_log("IRONHIDE_GATE: skip burn_stack (target_burning=%d, burned_this_hit=%d)",
                          target_already_burning, s_ironhide_burned_this_hit);
                *out_res = 0;
                return 1;
            }
        } else {
            if (target_already_burning) {
                skill_log("IRONHIDE_GATE: skip initial burn because target is already burning");
                *out_res = 0;
                return 1;
            }
        }
    }

    return 0;
}

static void ironhide_on_test_roll_post(SkillTestRollContext* ctx, int roll_result) {
    if (!ctx || !ctx->modifier_id) return;
    if (roll_result && strstr(ctx->modifier_id, "ironhide_missile_burn") != NULL) {
        s_ironhide_burned_this_hit = 1;
    }
}

static void ironhide_on_attack_start(int player_index, int action_type) {
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "ironhide") == NULL) return;
    // 重击 / SP1 / SP2 起手获得导弹暴击率增益 (0.8s)
    if (action_type == 4 || action_type == 0x100 || action_type == 16 || action_type == 32 ||
        action_type == 0x201 || action_type == 0x202) {
        skill_apply_buff_dur(player_index, "ironhide_missile_crit", 0.8f);
    }
}

static void ironhide_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2 || entered != 0) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "ironhide_gs") == NULL) return;

    if (sp_level == 1) {
        skill_apply_buff_dur(player_index, "ironhide_sp1_melee_buff", 8.0f);
        skill_log("IRONHIDE_GS: P%d SP1 expired -> granted ironhide_sp1_melee_buff (8.0s)", player_index);
    } else if (sp_level == 2) {
        skill_apply_buff_dur(player_index, "ironhide_sp2_unstoppable", 7.0f);
        skill_set_unstoppable(player_index, 7000);
        s_ironhide_gs_sp2_armor_ms[player_index] = skill_now_ms() + 7000;
        skill_log("IRONHIDE_GS: P%d SP2 expired -> granted unstoppable (7.0s), queued armor_up", player_index);
    }
}

static void ironhide_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_ironhide_gs_sp2_armor_ms[p] > 0 && now_ms >= s_ironhide_gs_sp2_armor_ms[p]) {
            s_ironhide_gs_sp2_armor_ms[p] = 0;
            const char* bid = skill_get_bot_id(p);
            if (bid && strstr(bid, "ironhide_gs") != NULL) {
                for (int i = 0; i < 3; i++) {
                    skill_apply_buff_dur(p, "ironhide_sp2_armor_up", 10.0f);
                }
                skill_log("IRONHIDE_GS: P%d SP2 unstoppable ended -> granted 3x ironhide_sp2_armor_up (10.0s)", p);
            }
        }
    }
}

BotSkillModule g_module_ironhide = {
    .bot_prefix        = "ironhide",
    .display_name_zh   = "铁皮",
    .on_hit_begin      = ironhide_on_hit_begin,
    .on_attack_start   = ironhide_on_attack_start,
    .on_test_roll      = ironhide_on_test_roll,
    .on_test_roll_post = ironhide_on_test_roll_post,
    .on_fight_reset    = ironhide_on_fight_reset,
    .on_special_state  = ironhide_on_special_state,
    .on_simulation_tick = ironhide_on_simulation_tick,
};
