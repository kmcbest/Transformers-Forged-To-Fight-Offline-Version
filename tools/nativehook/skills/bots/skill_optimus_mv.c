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
//    如果擎天柱正在流血状态，造成所有伤害的 35% 转化为自身生命值 (吸血)。
//    身上最多只能被施加一层流血，超过一层的流血会在一秒后被净化 (显示文字“净化”)，
//    并转化为擎天柱最大能量的 10% (0.30格)。
// 4. [2713] SP1：流血 (Bleed, E401)
//    SP1 60% 几率施加流血，造成 40% 攻击力伤害持续 4 秒。
// 5. [2729] SP1：伤害增益 (Damage Buff, E406)
//    随失去生命值动态增伤，最高 +150% (50% HP 时增伤 75%)。
// 6. [2727] SP2：流血 (Bleed, E401)
//    前两击每一击 90% 几率施加流血，造成 40% 攻击力伤害持续 4 秒。
// ===========================================================================

extern char g_p0_bot_id[80];
extern char g_p1_bot_id[80];

static uint64_t s_opt_armor_buff_end_ms[2]   = {0, 0};
static uint64_t s_opt_melee_buff_end_ms[2]   = {0, 0};
static uint64_t s_opt_pending_purify_ms[2]   = {0, 0};

static void optimus_mv_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // -----------------------------------------------------------------------
    // A. 擎天柱作为受击方 (Target)
    // -----------------------------------------------------------------------
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "optimusprime_cin_tf") != NULL) {
        int tp = ctx->target_player_index;

        // 1. [2724] 护甲增益减伤结算 (减伤 16.5%)
        // 由进入格挡姿态事件触发施加 optimusprime_cin_tf_block_armor (7s)
        int has_armor = skill_has_buff(tp, "optimusprime_cin_tf_block_armor") ||
                        skill_has_buff(tp, "block_armor") ||
                        (now_ms < s_opt_armor_buff_end_ms[tp]);
        if (has_armor) {
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

        // 近战增益伤害加成 (支持真实 Buff 容器检索与本地时间戳双重保障，仅限近战攻击)
        int has_melee = skill_has_buff(ap, "optimusprime_cin_tf_melee_buff") ||
                        skill_has_buff(ap, "melee_buff") ||
                        (now_ms < s_opt_melee_buff_end_ms[ap]);
        if (has_melee && !ctx->is_ranged) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= 1.60f; // +60% 近战伤害
            skill_log("OPTIMUS_MV: Melee Buff boosted damage on P%d: %.1f -> %.1f", ap, old_dmg, ctx->modified_damage);
        }

        // 3. [2726] 意志力吸血回生：处于流血状态时，造成的 35% 伤害转化为自身生命
        if (skill_has_buff(ap, "bleed")) {
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

static void optimus_mv_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    uint64_t now_ms = skill_now_ms();

    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "optimusprime_cin_tf") != NULL) {
        int tp = ctx->target_player_index;
        if (strstr(ctx->modifier_id, "block_armor") != NULL || strstr(ctx->modifier_id, "armor_up") != NULL) {
            float dur = (ctx->override_duration > 0.0f) ? ctx->override_duration : 7.0f;
            s_opt_armor_buff_end_ms[tp] = now_ms + (uint64_t)(dur * 1000.0f);
        } else if (strstr(ctx->modifier_id, "melee_buff") != NULL) {
            float dur = (ctx->override_duration > 0.0f) ? ctx->override_duration : 4.0f;
            s_opt_melee_buff_end_ms[tp] = now_ms + (uint64_t)(dur * 1000.0f);
        }
    }

    // 检查是否为施加给电影擎天柱的流血
    if (strstr(ctx->modifier_id, "bleed") != NULL &&
        ctx->target_bot_id && strstr(ctx->target_bot_id, "optimusprime_cin_tf") != NULL) {
        int tp = ctx->target_player_index;
        int bleed_count = skill_count_buffs(tp, "bleed");

        // 若当前流血层数超过 1 层，启动 1 秒后净化定时器
        if (bleed_count > 1) {
            if (s_opt_pending_purify_ms[tp] == 0) {
                s_opt_pending_purify_ms[tp] = now_ms + 1000;
                skill_log("OPTIMUS_MV: P%d received extra bleed (count=%d), scheduled purify in 1000ms", tp, bleed_count);
            }
        }
    }
}

static void optimus_mv_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bot_id = (p == 0) ? g_p0_bot_id : g_p1_bot_id;
        if (!bot_id || strstr(bot_id, "optimusprime_cin_tf") == NULL) {
            continue;
        }

        int bleed_count = skill_count_buffs(p, "bleed");
        if (bleed_count > 1) {
            // 如果多余流血尚未开启 1 秒倒计时，则启动倒计时
            if (s_opt_pending_purify_ms[p] == 0) {
                s_opt_pending_purify_ms[p] = now_ms + 1000;
                skill_log("OPTIMUS_MV: P%d has %d bleed stacks > 1, scheduled purify in 1000ms", p, bleed_count);
            } else if (now_ms >= s_opt_pending_purify_ms[p]) {
                s_opt_pending_purify_ms[p] = 0;

                // 1. 净化 1 层多余流血 (若有 dmg_bleed 优先净化，若无则净化通用 bleed)
                if (skill_has_buff(p, "dmg_bleed")) {
                    skill_consume_buff(p, "dmg_bleed", 1);
                } else {
                    skill_consume_buff(p, "bleed", 1);
                }

                // 2. 呼出净化提示文字并弹字 Callout ("净化")
                skill_apply_buff_dur(p, "optimusprime_cin_tf_purify", 1.5f);
                skill_overlay("[%s] 意志力：净化！流血转化为 +10%% 能量", p == 0 ? "电影擎天柱" : "敌方擎天柱");
                skill_log("OPTIMUS_MV: Purified 1 extra bleed on P%d -> granted 10%% mana (+0.30)", p);

                // 3. 转化为 10% 最大能量 (3格的10% = 0.30格)
                skill_add_mana(p, 0.30f);

                // 若净化后仍有多余流血则继续排队 1 秒后净化下一层
                if (skill_count_buffs(p, "bleed") > 1) {
                    s_opt_pending_purify_ms[p] = now_ms + 1000;
                }
            }
        } else {
            s_opt_pending_purify_ms[p] = 0;
        }
    }
}

static void optimus_mv_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_opt_armor_buff_end_ms[player_index] = 0;
        s_opt_melee_buff_end_ms[player_index] = 0;
        s_opt_pending_purify_ms[player_index] = 0;
    }
}

BotSkillModule g_module_optimus_mv = {
    .bot_prefix         = "optimusprime_cin_tf",
    .on_hit_connected   = optimus_mv_on_hit_connected,
    .on_buff_gated      = NULL,
    .on_buff_applied    = optimus_mv_on_buff_applied,
    .on_evade_check     = NULL,
    .on_test_roll       = NULL,
    .on_fight_reset     = optimus_mv_on_fight_reset,
    .on_simulation_tick = optimus_mv_on_simulation_tick,
};
