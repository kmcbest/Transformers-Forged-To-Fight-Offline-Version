#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 警车 (Prowl) 技能模块
// Bot ID: prowl_gs_deluxe2016
// ===========================================================================
// 1. [2727] 被动：近战增益 (Melee Buff)
//    后闪充能，每0.5s一层最多10层；充到10层或打断后转化为橙色近战增益，每层+11%近战伤害，持续6秒。
//    打断条件：
//      - 近战打中对手，打断
//      - 主动前冲，打断
//      - 放S技，无论打没打中，都打断
//      - 被对方击中，打断
//      - 触发规避，打断
//      - 远程射击小枪：不打断
// 2. [2736] SP2：远程伤害增益 (Ranged Damage Boost)
//    获得 6.0s 远程伤害+50%, 远程射速+50%。
// ===========================================================================

static void prowl_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "prowl") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 0. SP1 第一击命中对手时施加能量燃烧 (0.5s 抽取 1.215 格能量)
        if (ctx->special_index == 1 && ctx->hit_index == 0) {
            skill_apply_buff(tp, "prowl_s1_power_burn");
            skill_log("PROWL_SP1_BURN: hit 0 applied prowl_s1_power_burn to P%d", tp);
        }

        // 1. 放S技打断充能 (作为双保险，无论命中与否均打断)
        if (ctx->special_index > 0) {
            if (skill_prowl_is_charging(ap)) {
                skill_prowl_finish_charge(ap, "special attack hit");
            }
        }

        // 2. 近战攻击命中：
        // a) 打断充能 (仅限近战打中对手，远程小枪命中不打断)
        // b) 橙色近战增益：仅对近战攻击生效 (非远程且非特殊技)，每层 +11% 近战伤害 (最多 10 层，即 +110%)
        if (!ctx->is_ranged && ctx->special_index == 0) {
            if (skill_prowl_is_charging(ap)) {
                skill_prowl_finish_charge(ap, "melee attack hit opponent");
            }
            int stacks = skill_get_prowl_melee_stacks(ap);
            if (stacks > 0) {
                float boost = 1.0f + (0.11f * (float)stacks);
                float old_dmg = ctx->modified_damage;
                ctx->modified_damage *= boost;
                skill_log("PROWL: Melee damage boosted x%.2f (%.1f -> %.1f, stacks=%d) on P%d",
                          boost, old_dmg, ctx->modified_damage, stacks, ap);
            }
        }
    }
}

static void prowl_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return;

    if (strstr(ctx->modifier_id, "prowl_s2_ranged_boost") != NULL) {
        int tp = ctx->target_player_index;
        skill_set_ranged_boost(tp, 6000, 0.50f, 0.50f);
        skill_log("RANGED_BOOST_ACTIVATED: Prowl SP2 on P%d (dmg=+50%%, spd=+50%%, dur=6.0s)", tp);
    }
}

static uint64_t s_prowl_last_shot_ms[2] = {0, 0};

static int prowl_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strstr(ctx->modifier_id, "prowl_melee_charge") != NULL ||
        strstr(ctx->modifier_id, "prowl_passive_melee_buff") != NULL) {
        *out_res = 0; // 阻止原生自动触发，由后闪与转换时统一施加
        return 1;
    }

    // 远程眩晕: 仅远程射击生效; 连开三枪仅第一枪 roll dice; 充能中几率 80%，否则 10%
    if (strstr(ctx->modifier_id, "prowl_ranged_stun") != NULL) {
        if (!ctx->is_ranged) {
            *out_res = 0;
            return 1;
        }
        int p = (ctx->owner_player_index == 0) ? 0 : 1;
        uint64_t now_ms = skill_now_ms();
        if (now_ms - s_prowl_last_shot_ms[p] < 1000) {
            skill_log("PROWL_RANGED_STUN: skipping non-first shot in volley (elapsed=%llu ms)",
                      (unsigned long long)(now_ms - s_prowl_last_shot_ms[p]));
            *out_res = 0;
            return 1;
        }
        s_prowl_last_shot_ms[p] = now_ms;

        int is_charging = skill_prowl_is_charging(p);
        float chance = is_charging ? 0.80f : 0.10f;
        if (ctx->p_chance) *ctx->p_chance = chance;

        float r = skill_random_float();
        if (ctx->p_roll) *ctx->p_roll = r;

        skill_log("PROWL_RANGED_STUN_ROLL: [P%d] charging=%d chance=%.2f roll=%.3f", p, is_charging, chance, r);
        if (r < chance) {
            skill_overlay("[P%d] 远程眩晕命中！(几率: %.0f%%)", p, chance * 100.0f);
            *out_res = 1;
        } else {
            *out_res = 0;
        }
        return 1;
    }

    return 0;
}

static void prowl_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_prowl_last_shot_ms[player_index] = 0;
    }
}

BotSkillModule g_module_prowl = {
    .bot_prefix = "prowl",
    .display_name_zh = "警车",
    .on_hit_connected = prowl_on_hit_connected,
    .on_buff_gated = NULL,
    .on_buff_applied = prowl_on_buff_applied,
    .on_evade_check = NULL,
    .on_test_roll = prowl_on_test_roll,
    .on_fight_reset = prowl_on_fight_reset
};
