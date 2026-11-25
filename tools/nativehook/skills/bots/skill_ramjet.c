#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 喷气机 (Ramjet) 技能模块
// 迁移自 hook.c: SP1 随机 1~4 层燃烧叠层门禁

static int s_ramjet_s1_stacks = 0;

static void ramjet_on_hit_begin(void) {
    s_ramjet_s1_stacks = 0;
}

static void ramjet_on_fight_reset(int player_index) {
    (void)player_index;
    s_ramjet_s1_stacks = 0;
}

static int ramjet_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strstr(ctx->modifier_id, "ramjet_s1_burn_stack_") != NULL) {
        int stack_idx = 2;
        if (strstr(ctx->modifier_id, "stack_3") != NULL) stack_idx = 3;
        else if (strstr(ctx->modifier_id, "stack_4") != NULL) stack_idx = 4;

        *out_res = (s_ramjet_s1_stacks >= stack_idx) ? 1 : 0;
        return 1;
    }

    if (strstr(ctx->modifier_id, "ramjet_heavy_burn_stun") != NULL) {
        if (!skill_is_burning(ctx->target_player_index)) {
            *out_res = 0;
            return 1;
        }
    }

    return 0;
}

static void ramjet_on_test_roll_post(SkillTestRollContext* ctx, int roll_result) {
    if (!ctx || !ctx->modifier_id) return;

    if (strcmp(ctx->modifier_id, "ramjet_s1_burn") == 0) {
        if (roll_result) {
            int n = 1 + (int)(skill_random_float() * 4.0f);
            if (n < 1) n = 1;
            if (n > 4) n = 4;
            s_ramjet_s1_stacks = n;
            float roll_v = ctx->p_roll ? *ctx->p_roll : 0.0f;
            float chance_v = ctx->p_chance ? *ctx->p_chance : 0.0f;
            skill_log("RAMJET_SP1_ROLL: passed, decided target stacks = %d (roll=%.3f, chance=%.3f)",
                      s_ramjet_s1_stacks, roll_v, chance_v);
            skill_overlay("[喷气机] SP1 燃烧 PASS! +%d层! (Roll: %.1f%% < %.1f%%)",
                          s_ramjet_s1_stacks, roll_v * 100.0f, chance_v * 100.0f);
        } else {
            s_ramjet_s1_stacks = 0;
        }
    }
}

BotSkillModule g_module_ramjet = {
    .bot_prefix        = "ramjet",
    .display_name_zh   = "喷气机",
    .on_hit_begin      = ramjet_on_hit_begin,
    .on_test_roll      = ramjet_on_test_roll,
    .on_test_roll_post = ramjet_on_test_roll_post,
    .on_fight_reset    = ramjet_on_fight_reset,
};
