#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 黄蜂勇士 (Waspinator) 技能模块
// 迁移自 hook.c & 补齐低血量被动与 SP1/SP2 末击收口

static int s_wasp_ranged_on[2] = {0, 0};
static int s_wasp_sp_dmg_on[2] = {0, 0};

static void waspinator_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_wasp_ranged_on[player_index] = 0;
        s_wasp_sp_dmg_on[player_index] = 0;
    }
}

static void waspinator_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "waspinator") == NULL) continue;
        float hp_ratio = skill_get_hp_ratio(p);
        if (hp_ratio <= 0.50f && !s_wasp_ranged_on[p]) {
            s_wasp_ranged_on[p] = 1;
            skill_apply_buff(p, "waspinator_sig_ranged_speed");
            skill_apply_buff(p, "waspinator_passive_ranged_speed");
        }
        if (hp_ratio <= 0.25f && !s_wasp_sp_dmg_on[p]) {
            s_wasp_sp_dmg_on[p] = 1;
            skill_apply_buff(p, "waspinator_low_hp_sp_dmg");
        }
    }
}

static int waspinator_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strstr(ctx->modifier_id, "waspinator_s3_burn") != NULL ||
        strstr(ctx->modifier_id, "waspinator_sp1_anti_evade") != NULL ||
        strstr(ctx->modifier_id, "waspinator_sp2_resist_debuff") != NULL) {
        if (!ctx->current_hit_is_last) {
            skill_log("WASPINATOR_GATE: non-last hit, skip roll: %s", ctx->modifier_id);
            *out_res = 0;
            return 1;
        }
    }

    return 0;
}

BotSkillModule g_module_waspinator = {
    .bot_prefix         = "waspinator",
    .display_name_zh    = "黄蜂勇士",
    .on_test_roll       = waspinator_on_test_roll,
    .on_simulation_tick = waspinator_on_simulation_tick,
    .on_fight_reset     = waspinator_on_fight_reset,
};
