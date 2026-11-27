#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 威震天 (Megatron Leader 2015) 技能模块
// Bot ID: megatron_gs_leader2015
// ===========================================================================
// 1. [3121] 被动：融合炮充能 (Fusion Cannon Charge)
//    - 开局显现灰色 6 秒倒计时图标 (\uE910)，每 6 秒充满 1 层紫色融合炮图标 (上限 3 层)。
//    - 满 3 层时倒计时隐藏暂停；消耗后重新开始 6 秒倒计时。
//    - 拥有融合炮（>=1层或过载）时，重击飞行速度 +50%、伤害 +30%，重击命中消耗 1 层（过载时不消耗）。
// 2. [3138] 被动：减益融合 (Debuff Fusion, \uE60F)
//    - 拥有融合炮且重击命中时，将对方身上全部带倒计时的减益转化为无倒计时永久状态，并呼出“减益融合”。
// 3. [被动] 近战刷新 (Melee Refresh)
//    - 用 M2 击中（未格挡）对手会刷新对方身上所有带倒计时减益的持续时间。
// 4. [3126] 被动：不可阻挡 (Unstoppable, \uE915)
//    - 被击倒后，威震天有概率获得 3 秒不可阻挡，概率 = 损失生命百分比 * 0.70。
// 5. [3127] 觉醒技：毫不留情 (No Mercy)
//    - 只要对手身上有融合的（永久）减益，威震天的近战攻击（打中和被防都算）
//      有 60% 概率从对方身上随机偷走 1 层增益，持续 5 秒（偷永久增益也会在 5 秒后过期）。
// 6. [3137] SP1：破甲 38% (10s) 并清除对手护甲增益。
// 7. [3129] SP2：攻击减益 44% (10s)。
// 8. [3130] SP3：震击 300% (20s) + 融合炮过载（图标变绿，不带数字，本局无限使用不消耗）。
// ===========================================================================

static int      s_megatron_active[2]  = {0, 0};
static int      s_fusion_charges[2]   = {0, 0};
static uint64_t s_last_charge_ms[2]   = {0, 0};
static int      s_fusion_overload[2]  = {0, 0};
static int      s_kd_pending[2]       = {0, 0};
static uint64_t s_kd_pending_ms[2]    = {0, 0};

static int megatron_is_self(const char* bot_id) {
    return (bot_id && strstr(bot_id, "megatron_gs") != NULL);
}

static void megatron_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (!megatron_is_self(skill_get_bot_id(p))) continue;

        // 0. 被击倒起身阶段触发【不可阻挡】(击中倒地 1200ms 后起身瞬时判定，绝不在撞击前抢发)
        if (s_kd_pending[p] && now_ms >= s_kd_pending_ms[p] + 1200ULL) {
            s_kd_pending[p] = 0;
            s_kd_pending_ms[p] = 0;
            if (!skill_is_unstoppable(p)) {
                float hp_ratio = skill_get_hp_ratio(p);
                float lost_ratio = 1.0f - hp_ratio;
                if (lost_ratio < 0.0f) lost_ratio = 0.0f;
                if (lost_ratio > 1.0f) lost_ratio = 1.0f;
                float chance = lost_ratio * 0.70f;
                float roll = skill_random_float();
                if (chance > 0.0f && roll < chance) {
                    skill_apply_buff_dur(p, "megatron_knockdown_unstoppable", 3.0f);
                    skill_overlay("[%s] 被击倒起身！触发不可阻挡 (3秒, 概率%.0f%%)",
                                  p == 0 ? "威震天" : "敌方威震天", chance * 100.0f);
                    skill_log("MEGATRON_KD_UNSTOPPABLE: P%d knocked down (lost=%.1f%%, chance=%.1f%%, roll=%.3f) -> 3.0s unstoppable on wakeup",
                              p, lost_ratio * 100.0f, chance * 100.0f, roll);
                } else {
                    skill_log("MEGATRON_KD_UNSTOPPABLE: P%d knocked down (lost=%.1f%%, chance=%.1f%%, roll=%.3f) -> missed",
                              p, lost_ratio * 100.0f, chance * 100.0f, roll);
                }
            }
        }

        if (!s_megatron_active[p] || s_fusion_overload[p]) continue;

        int cur_charges = skill_count_buffs(p, "megatron_fusion_cannon");
        s_fusion_charges[p] = cur_charges;

        if (cur_charges < 3) {
            if (s_last_charge_ms[p] == 0) {
                s_last_charge_ms[p] = now_ms;
                if (!skill_has_buff(p, "megatron_fusion_cd")) {
                    skill_apply_buff_dur(p, "megatron_fusion_cd", 6.0f);
                }
            } else if (now_ms >= s_last_charge_ms[p] && (now_ms - s_last_charge_ms[p] >= 6000)) {
                skill_consume_buff(p, "megatron_fusion_cd", 1);
                skill_apply_buff_dur(p, "megatron_fusion_cannon", -1.0f);
                cur_charges = skill_count_buffs(p, "megatron_fusion_cannon");
                s_fusion_charges[p] = cur_charges;
                skill_overlay("[%s] 融合炮充能完成 (%d/3)",
                              p == 0 ? "威震天" : "敌方威震天", cur_charges);
                skill_log("MEGATRON: P%d gained Fusion Cannon stack %d/3", p, cur_charges);

                if (cur_charges < 3) {
                    s_last_charge_ms[p] = now_ms;
                    skill_apply_buff_dur(p, "megatron_fusion_cd", 6.0f);
                } else {
                    s_last_charge_ms[p] = 0; // 满 3 层停止倒计时
                }
            }
        }
    }
}

static void megatron_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    if (ctx->hit_flags & (2 | 512 | 1024)) return;
    uint64_t now_ms = skill_now_ms();

    // -----------------------------------------------------------------------
    // 0. 攻击减益与(模拟器)破甲结算：
    //    C# 引擎不自动从 attack_debuff 扣减攻击输出，此处统一对任何持 megatron_sp2_atk_debuff 的攻击方结算 -44%
    // -----------------------------------------------------------------------
    int att_p = ctx->attacker_player_index;
    int def_p = ctx->target_player_index;
    if (att_p >= 0 && att_p < 2) {
        int atk_debuff_stacks = skill_count_buffs(att_p, "megatron_sp2_atk_debuff");
        if (atk_debuff_stacks > 0) {
            float mult = 1.0f - 0.44f * (float)atk_debuff_stacks;
            if (mult < 0.10f) mult = 0.10f;
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= mult;
            skill_log("MEGATRON_ATK_DEBUFF: Attacker P%d weakened x%.2f (stacks=%d, %.1f -> %.1f)",
                      att_p, mult, atk_debuff_stacks, old_dmg, ctx->modified_damage);
        }
    }
#ifndef __ANDROID__
    if (def_p >= 0 && def_p < 2) {
        int ab_stacks = skill_count_buffs(def_p, "megatron_sp1_armor_break");
        if (ab_stacks > 0) {
            ctx->modified_damage *= (1.0f + 0.38f * (float)ab_stacks);
        }
    }
#endif

    // -----------------------------------------------------------------------
    // 1. 威震天作为受击方：记录被击倒事件（起身 1200ms 后在 tick 中结算不可阻挡，不抢发在撞击前）
    // -----------------------------------------------------------------------
    if (megatron_is_self(ctx->target_bot_id) && !ctx->is_blocked && def_p >= 0 && def_p < 2) {
        int sp_in = ctx->special_index;
        if (sp_in == 0) {
            if (ctx->action_type == 16) sp_in = 1;
            else if (ctx->action_type == 32) sp_in = 2;
            else if (ctx->action_type == 64) sp_in = 3;
        }
        int is_knockdown_hit = (ctx->is_last_hit && (ctx->is_heavy || sp_in > 0));
        if (is_knockdown_hit && (sp_in == 3 || !skill_is_unstoppable(def_p))) {
            s_kd_pending[def_p] = 1;
            s_kd_pending_ms[def_p] = now_ms;
            skill_log("MEGATRON_KD_ARMED: P%d knocked down (sp=%d heavy=%d), arming wakeup unstoppable check (+1200ms)",
                      def_p, sp_in, ctx->is_heavy ? 1 : 0);
        }
    }

    // -----------------------------------------------------------------------
    // 2. 威震天作为攻击方
    // -----------------------------------------------------------------------
    if (!megatron_is_self(ctx->attacker_bot_id)) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    if (ap < 0 || ap >= 2 || tp < 0 || tp >= 2) return;

    int sp = ctx->special_index;
    if (sp == 0) {
        if (ctx->action_type == 16) sp = 1;
        else if (ctx->action_type == 32) sp = 2;
        else if (ctx->action_type == 64) sp = 3;
    }

    // (2a) 觉醒技【毫不留情】：只要对手身上有融合的（永久）减益，
    //      近战攻击（轻/中/重，打中和被防都算！）60% 概率从对方身上随机偷走 1 层增益，持续 5 秒。
    if (sp == 0 && !ctx->is_ranged) {
        if (skill_has_fused_debuff(tp)) {
            float roll = skill_random_float();
            if (roll < 0.60f) {
                char stolen_id[64] = {0};
                if (skill_steal_random_buff(ap, tp, 5.0f, stolen_id, sizeof(stolen_id))) {
                    skill_apply_buff_dur(ap, "megatron_no_mercy_steal", 1.5f);
                    skill_overlay("[%s] 毫不留情！窃取 [%s] (5秒)",
                                  ap == 0 ? "威震天" : "敌方威震天", stolen_id);
                    skill_log("MEGATRON_NO_MERCY: P%d melee (blk=%d) stole '%s' from P%d for 5.0s (roll=%.3f < 0.60)",
                              ap, ctx->is_blocked ? 1 : 0, stolen_id, tp, roll);
                }
            } else {
                skill_log("MEGATRON_NO_MERCY: P%d melee (blk=%d) fused debuff active, roll=%.3f >= 0.60",
                          ap, ctx->is_blocked ? 1 : 0, roll);
            }
        }
    }

    // 以下效应均要求未被格挡命中
    if (ctx->is_blocked) return;

    // (2b) 被动【近战刷新】：用 M2 击中对手刷新其身上所有带倒计时减益的持续时间
    int is_m2 = (sp == 0 && !ctx->is_ranged && ctx->action_type == 2 &&
                 (skill_get_combo_medium_index(ap) >= 2 || ctx->hit_index == 1));
    if (is_m2) {
        int refreshed = skill_refresh_target_debuffs(tp);
        if (refreshed > 0) {
            skill_apply_buff_dur(ap, "megatron_melee_refresh", 1.2f);
            skill_overlay("[%s] 近战刷新！重置对手全部减益倒计时！",
                          ap == 0 ? "威震天" : "敌方威震天");
            skill_log("MEGATRON_MELEE_REFRESH: P%d M2 refreshed timed debuffs on P%d (count=%d)",
                      ap, tp, refreshed);
        }
    }

    // (2c) 被动【融合炮 + 减益融合】：仅普通重击触发（过载或至少 1 层融合炮时）
    if (sp == 0 && ctx->is_heavy) {
        int live_charges = skill_count_buffs(ap, "megatron_fusion_cannon");
        int has_fusion = (s_fusion_overload[ap] || live_charges > 0);
        s_fusion_charges[ap] = live_charges;

        skill_log("MEGATRON: P%d heavy hit connected (last=%d, overload=%d, charges=%d)",
                  ap, ctx->is_last_hit, s_fusion_overload[ap], live_charges);

        if (has_fusion) {
            ctx->modified_damage *= 1.30f;

            if (!s_fusion_overload[ap]) {
                skill_consume_buff(ap, "megatron_fusion_cannon", 1);
                s_fusion_charges[ap] = skill_count_buffs(ap, "megatron_fusion_cannon");
                skill_log("MEGATRON: P%d consumed 1 Fusion stack, remaining %d/3",
                          ap, s_fusion_charges[ap]);

                if (s_fusion_charges[ap] < 3 && s_last_charge_ms[ap] == 0) {
                    s_last_charge_ms[ap] = now_ms;
                    skill_apply_buff_dur(ap, "megatron_fusion_cd", 6.0f);
                }
            }

            int fused = skill_fuse_target_debuffs(tp);
            if (fused > 0) {
                skill_apply_buff_dur(ap, "megatron_debuff_fusion", 1.5f);
                skill_overlay("[%s] 减益融合！固化对手 %d 个减益为永久！",
                              ap == 0 ? "威震天" : "敌方威震天", fused);
                skill_log("MEGATRON: P%d successfully FUSED %d debuffs on P%d to permanent!",
                          ap, fused, tp);
            } else {
                skill_log("MEGATRON: P%d heavy hit with fusion, but opponent P%d has no timed debuffs to fuse",
                          ap, tp);
            }
        }
    }

    // (2d) SP1 / SP2 / SP3 末击效应
    if (sp > 0 && ctx->is_last_hit) {
        if (sp == 1) {
            // 移除对手全部护甲增益并 100% 施加 38% 破甲 (10秒)
            for (int i = 0; i < 16; i++) {
                if (!skill_dispel_random_buff_by_category(tp, 0, 1, NULL, 0)) {
                    break;
                }
            }
            skill_apply_buff_dur(tp, "megatron_sp1_armor_break", 10.0f);
            skill_overlay("[%s] SP1 粉碎重击！移除护甲并施加 38%% 破甲 (10秒)",
                          ap == 0 ? "威震天" : "敌方威震天");
            skill_log("MEGATRON_SP1: P%d lastHit dispelled armor & applied 38%% armor break (10s) to P%d", ap, tp);
        } else if (sp == 2) {
            // 100% 施加 44% 攻击减益 (10秒)
            skill_apply_buff_dur(tp, "megatron_sp2_atk_debuff", 10.0f);
            skill_overlay("[%s] SP2 毁灭光束！施加 44%% 攻击减益 (10秒)",
                          ap == 0 ? "威震天" : "敌方威震天");
            skill_log("MEGATRON_SP2: P%d lastHit applied 44%% atk debuff (10s) to P%d", ap, tp);
        } else if (sp == 3) {
            // 100% 施加 300% 震击 (20秒) + 融合炮永久过载
            skill_apply_buff_dur(tp, "megatron_sp3_shock", 20.0f);
            skill_log("MEGATRON_SP3: P%d lastHit applied 300%% shock (20s) to P%d", ap, tp);
            if (!s_fusion_overload[ap]) {
                s_fusion_overload[ap] = 1;
                s_fusion_charges[ap] = 0;
                s_last_charge_ms[ap] = 0;
                skill_consume_buff(ap, "megatron_fusion_cd", 99);
                skill_consume_buff(ap, "megatron_fusion_cannon", 99);
                skill_apply_buff_dur(ap, "megatron_fusion_overload", -1.0f);
                skill_overlay("[%s] 融合炮过载！本局无限全功率重击，不消耗层数！",
                              ap == 0 ? "威震天" : "敌方威震天");
                skill_log("MEGATRON: P%d activated SP3 Fusion Cannon Overload!", ap);
            }
        }
    }
}

static void megatron_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    if (!megatron_is_self(ctx->target_bot_id)) return;

    int tp = ctx->target_player_index;
    if (tp < 0 || tp > 1) return;

    if (strcmp(ctx->modifier_id, "megatron_fusion_cd") == 0) {
        s_megatron_active[tp] = 1;
        if (s_last_charge_ms[tp] == 0) {
            s_last_charge_ms[tp] = skill_now_ms();
            skill_log("MEGATRON: Initial 6s Fusion Cannon CD started on P%d", tp);
        }
        return;
    }
    if (strcmp(ctx->modifier_id, "megatron_fusion_cannon") == 0) {
        s_megatron_active[tp] = 1;
        s_fusion_charges[tp] = skill_count_buffs(tp, "megatron_fusion_cannon");
        skill_log("MEGATRON: P%d Fusion Cannon stack synced to %d/3", tp, s_fusion_charges[tp]);
        return;
    }
    if (strcmp(ctx->modifier_id, "megatron_fusion_overload") == 0) {
        s_megatron_active[tp] = 1;
        s_fusion_overload[tp] = 1;
        s_last_charge_ms[tp] = 0;
        return;
    }
}

static int megatron_on_projectile_speed(int player_index, int is_heavy, float* out_speed_mult) {
    if (player_index < 0 || player_index >= 2 || !out_speed_mult) return 0;
    if (!megatron_is_self(skill_get_bot_id(player_index))) return 0;

    int live_charges = skill_count_buffs(player_index, "megatron_fusion_cannon");
    if (is_heavy && (s_fusion_overload[player_index] || live_charges > 0)) {
        *out_speed_mult = 1.50f;
        skill_log("MEGATRON: P%d Fusion Cannon Heavy Attack projectile speed boosted +50%% (overload=%d, charges=%d)",
                  player_index, s_fusion_overload[player_index], live_charges);
        return 1;
    }
    return 0;
}

static int megatron_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strcmp(ctx->modifier_id, "megatron_fusion_cd") == 0) {
        if (ctx->p_chance) *ctx->p_chance = 1.0f;
        if (ctx->p_roll) *ctx->p_roll = 0.0f;
        *out_res = 1; // 开局自动激活 6 秒灰色融合炮倒计时图标
        return 1;
    }
    if (strcmp(ctx->modifier_id, "megatron_fusion_cannon") == 0 ||
        strcmp(ctx->modifier_id, "megatron_debuff_fusion") == 0 ||
        strcmp(ctx->modifier_id, "megatron_fusion_overload") == 0 ||
        strcmp(ctx->modifier_id, "megatron_melee_refresh") == 0 ||
        strcmp(ctx->modifier_id, "megatron_no_mercy_steal") == 0 ||
        strcmp(ctx->modifier_id, "megatron_knockdown_unstoppable") == 0) {
        *out_res = 0; // 由 C 逻辑精确触发
        return 1;
    }
    return 0;
}

static void megatron_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_megatron_active[player_index] = 0;
        s_fusion_charges[player_index]  = 0;
        s_last_charge_ms[player_index]  = 0;
        s_fusion_overload[player_index] = 0;
        s_kd_pending[player_index]      = 0;
        s_kd_pending_ms[player_index]   = 0;
    }
}

BotSkillModule g_module_megatron = {
    .bot_prefix          = "megatron",
    .display_name_zh     = "威震天",
    .on_hit_connected    = megatron_on_hit_connected,
    .on_buff_gated       = NULL,
    .on_buff_applied     = megatron_on_buff_applied,
    .on_evade_check      = NULL,
    .on_test_roll        = megatron_on_test_roll,
    .on_power_gain_rate  = NULL,
    .on_reflect_proj     = NULL,
    .on_projectile_speed = megatron_on_projectile_speed,
    .on_hitreact_enter   = NULL,
    .on_fight_reset      = megatron_on_fight_reset,
    .on_simulation_tick  = megatron_on_simulation_tick,
};
