#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 警车 (Prowl) 技能模块
// Bot ID: prowl_gs_deluxe2016
// ===========================================================================
// 1. [2727] 被动：近战增益 (Melee Buff)
//    后闪充能，每0.5s一层最多10层；充到10层或打断后转化为橙色近战增益，每层+11%近战伤害，持续6秒。
// 2. [2736] SP2：远程伤害增益 (Ranged Damage Boost)
//    获得 6.0s 远程伤害+50%, 远程射速+50%。
// ===========================================================================

static void prowl_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "prowl") != NULL) {
        int ap = ctx->attacker_player_index;
        // 警车橙色近战增益：仅对近战攻击生效，每层 +11% 近战伤害 (最多 10 层，即 +110%)
        if (!ctx->is_ranged) {
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
        skill_set_ranged_boost(0, 6000, 0.50f, 0.50f);
        skill_log("RANGED_BOOST_ACTIVATED: Prowl SP2 (dmg=+50%%, spd=+50%%, dur=6.0s)");
    }
}

static void prowl_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_prowl = {
    .bot_prefix = "prowl",
    .on_hit_connected = prowl_on_hit_connected,
    .on_buff_gated = NULL,
    .on_buff_applied = prowl_on_buff_applied,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_fight_reset = prowl_on_fight_reset
};
