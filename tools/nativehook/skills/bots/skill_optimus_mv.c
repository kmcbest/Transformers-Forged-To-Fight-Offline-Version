#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 电影擎天柱 (Optimus Prime MV1) 技能模块
// Bot ID: optimusprime_cin_tf
// ===========================================================================
// 1. [2724] 被动：护甲增益 (Armor Buff, 0xe517)
//    进入格挡姿态 100% 获得护甲，受到伤害降低 16.5%，持续 7 秒。
// 2. [2725] 被动：近战增益 (Melee Buff, E412)
//    所有攻击 10% 概率触发近战增益，近战伤害提升 60%，持续 4 秒 (唯一，刷新时长)。
// 3. [2726] 被动：意志力 (Willpower, E942)
//    流血状态下，造成所有伤害的 35% 转化为自身生命恢复 (吸血绿字)。
//    身上最多只能有一层流血，额外施加的流血被净化，转化为 10% 最大能量 (0.3格)。
// 4. [2713] SP1：流血 (Bleed, E401)
//    SP1 60% 几率施加流血，造成 40% 攻击力伤害持续 4 秒。
// 5. [2729] SP1：伤害增益 (Damage Buff, E406)
//    随失去生命值动态增伤，最高 +150% (50% HP 时增伤 75%)。
// 6. [2727] SP2：流血 (Bleed, E401)
//    前两击每一击 90% 几率施加流血，造成 40% 攻击力伤害持续 4 秒。
// ===========================================================================

static uint64_t s_opt_armor_buff_end_ms[2] = {0, 0};
static uint64_t s_opt_melee_buff_end_ms[2] = {0, 0};
static uint64_t s_opt_bleeding_end_ms[2]   = {0, 0};

static void optimus_mv_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // -----------------------------------------------------------------------
    // A. 擎天柱作为受击方 (Target)
    // -----------------------------------------------------------------------
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "optimusprime_cin_tf") != NULL) {
        int tp = ctx->target_player_index;

        // 1. [2724] 进入格挡姿态获得 7 秒护甲增益
        if (ctx->is_blocked) {
            s_opt_armor_buff_end_ms[tp] = now_ms + 7000;
            skill_overlay("[%s] 护甲增益激活 (减伤 16.5%%, 7s)", tp == 0 ? "电影擎天柱" : "敌方擎天柱");
            skill_log("OPTIMUS_MV: Armor Buff activated on player %d for 7.0s", tp);
        }

        // 护甲增益减伤结算
        if (now_ms < s_opt_armor_buff_end_ms[tp]) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= (1.0f - 0.165f); // 降低 16.5% 伤害
            skill_log("OPTIMUS_MV: Armor reduced damage on P%d: %.1f -> %.1f", tp, old_dmg, ctx->modified_damage);
        }
    }

    // -----------------------------------------------------------------------
    // B. 擎天柱作为攻击方 (Attacker)
    // -----------------------------------------------------------------------
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "optimusprime_cin_tf") != NULL) {
        int ap = ctx->attacker_player_index;

        // 2. [2725] 所有攻击 10% 几率触发近战增益 (4s)
        if (skill_random_float() < 0.10f) {
            s_opt_melee_buff_end_ms[ap] = now_ms + 4000;
            skill_overlay("[%s] 近战增益激活 (+60%% 近战伤害, 4s)", ap == 0 ? "电影擎天柱" : "敌方擎天柱");
            skill_log("OPTIMUS_MV: Melee Buff proc on P%d for 4.0s", ap);
        }

        // 近战增益伤害加成
        if (now_ms < s_opt_melee_buff_end_ms[ap] && !ctx->is_ranged) {
            ctx->modified_damage *= 1.60f; // +60% 近战伤害
        }

        // 3. [2726] 意志力吸血回生：处于流血状态时，造成的 35% 伤害转化为自身生命
        if (now_ms < s_opt_bleeding_end_ms[ap]) {
            float heal_amount = ctx->modified_damage * 0.35f;
            if (heal_amount > 0.0f) {
                skill_heal(ap, heal_amount);
                skill_overlay("[%s] 意志力吸血回生 (+%.0f HP)", ap == 0 ? "电影擎天柱" : "敌方擎天柱", heal_amount);
                skill_log("OPTIMUS_MV: Willpower lifesteal on P%d: +%.1f HP (35%% of %.1f)", ap, heal_amount, ctx->modified_damage);
            }
        }

        // 4. [2729] SP1 动态伤害加成：随损失生命值增伤，最高 +150% (50% HP 增伤 75%)
        if (ctx->special_index == 1) {
            float hp_ratio = skill_get_hp_ratio(ap);
            float loss_ratio = 1.0f - hp_ratio;
            if (loss_ratio < 0.0f) loss_ratio = 0.0f;
            if (loss_ratio > 1.0f) loss_ratio = 1.0f;
            float boost_mult = 1.0f + (loss_ratio * 1.50f);
            ctx->modified_damage *= boost_mult;
            skill_log("OPTIMUS_MV: SP1 dynamic damage on P%d: HP=%.1f%% -> dmg x%.2f (boost=+%.1f%%)",
                      ap, hp_ratio * 100.0f, boost_mult, (boost_mult - 1.0f) * 100.0f);

            // [2713] SP1 60% 几率施加流血 4 秒
            if (skill_random_float() < 0.60f) {
                skill_overlay("[%s] SP1 剑舞流血！(60%% 触发, 4s)", ap == 0 ? "电影擎天柱" : "敌方擎天柱");
            }
        }

        // 5. [2727] SP2 前两击 90% 几率施加流血 4 秒
        if (ctx->special_index == 2 && ctx->hit_index < 2) {
            if (skill_random_float() < 0.90f) {
                skill_overlay("[%s] SP2 守卫斩击流血！(90%% 触发, 4s)", ap == 0 ? "电影擎天柱" : "敌方擎天柱");
            }
        }
    }
}

static int optimus_mv_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id) return 0;
    uint64_t now_ms = skill_now_ms();

    // 判定目标是否为电影擎天柱
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "optimusprime_cin_tf") != NULL) {
        int tp = ctx->target_player_index;

        // [2726] 意志力流血净化与能量转化机制
        if (strstr(ctx->modifier_id, "bleed") != NULL) {
            // 如果身上当前已有流血生效
            if (now_ms < s_opt_bleeding_end_ms[tp]) {
                ctx->allow_application = false; // 净化/拦截第二层流血
                skill_add_mana(tp, 0.30f);       // 转化为 10% 最大能量 (3格的10% = 0.30格)
                skill_overlay("[%s] 意志力净化多余流血！转化为 +10%% 能量", tp == 0 ? "电影擎天柱" : "敌方擎天柱");
                skill_log("OPTIMUS_MV: Willpower purged duplicate bleed on P%d -> granted 0.30 mana (10%%)", tp);
                return 1; // 已处理
            } else {
                // 第一层流血放行并记录倒计时 4 秒
                s_opt_bleeding_end_ms[tp] = now_ms + 4000;
                ctx->allow_application = true;
                skill_log("OPTIMUS_MV: Willpower registered initial bleed on P%d for 4.0s", tp);
                return 1; // 已处理
            }
        }
    }

    return 0;
}

static void optimus_mv_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    uint64_t now_ms = skill_now_ms();
    if (strstr(ctx->modifier_id, "bleed") != NULL &&
        ctx->target_bot_id && strstr(ctx->target_bot_id, "optimusprime_cin_tf") != NULL) {
        int tp = ctx->target_player_index;
        float dur = (ctx->override_duration > 0.0f) ? ctx->override_duration : 4.0f;
        s_opt_bleeding_end_ms[tp] = now_ms + (uint64_t)(dur * 1000.0f);
        skill_overlay("[%s] 意志力生效中：造成伤害 35%% 转化为生命！", tp == 0 ? "电影擎天柱" : "敌方擎天柱");
    }
}


static void optimus_mv_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_opt_armor_buff_end_ms[player_index] = 0;
        s_opt_melee_buff_end_ms[player_index] = 0;
        s_opt_bleeding_end_ms[player_index]   = 0;
    }
}

BotSkillModule g_module_optimus_mv = {
    .bot_prefix = "optimusprime_cin_tf",
    .on_hit_connected = optimus_mv_on_hit_connected,
    .on_buff_gated = optimus_mv_on_buff_gated,
    .on_buff_applied = optimus_mv_on_buff_applied,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_fight_reset = optimus_mv_on_fight_reset
};
