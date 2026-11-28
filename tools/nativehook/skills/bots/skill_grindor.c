#include "../skill_env.h"
#include "../skill_types.h"
#include <string.h>

/*
 * 碾碎器 (grindor_cin_rotf) 战斗逻辑模块：
 * 1. 天然护甲：+17% 常驻减伤，无图标，不可被破甲移除
 * 2. 受击被动：8% 获 +41% 护甲增益（6 秒）；11% 对攻击方施加 1 层 -40% 暴击率减益（8 秒）
 * 3. 格挡精通削弱：对手每层碾碎器暴击率减益额外降低其 15% 格挡精通（基准 50%）
 * 4. 觉醒 贯穿：所有近战攻击（含 SP1/SP2/SP3 第 1 击）提升 110% * 敌方能量比例的伤害
 * 5. 重击：若暴击且未格挡 100% 施加 6 秒 80% 燃烧
 * 6. SP1：末击未格挡 100% 施加 8s -40% 暴击率减益；35% 锁定 SP2（6s）；75% 锁定 SP3（6s）
 * 7. SP2：按对手能量最高 +40% 额外伤害；末击未格挡 50% 锁定 SP3（6s）
 * 8. SP3：100% 锁定对手 SP2 与 SP3（10s，能量条渲染白锁）；100% 施加 1 层永久 -16% 暴击率减益；
 *         最后一击暴击率 +50%，若暴击 100% 施加 6 秒 80% 燃烧
 */

static int is_grindor(const char* bot_id) {
    return bot_id && strstr(bot_id, "grindor") != NULL;
}

static int grindor_crit_chance_mod(int player_index, int atk_level, float* out_bonus) {
    if (player_index < 0 || player_index >= 2 || !out_bonus) return 0;
    if (!is_grindor(skill_get_bot_id(player_index))) return 0;
    if (atk_level == 64 && skill_is_current_hit_last()) {
        *out_bonus = 0.50f;
        skill_log("GRINDOR_SP3: P%d last hit +50%% crit chance", player_index);
        return 1;
    }
    return 0;
}

static void grindor_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 1. 碾碎器作为受击方
    if (tp >= 0 && tp < 2 && is_grindor(ctx->target_bot_id)) {
        // 天然 +17% 常驻护甲（不可被破甲移除，无图标）
        float pre_nat = ctx->modified_damage;
        ctx->modified_damage *= (1.0f - 0.17f);
        skill_log("GRINDOR_NAT_ARMOR: P%d natural -17%% dmg (%.1f -> %.1f)",
                  tp, pre_nat, ctx->modified_damage);

#ifndef __ANDROID__
        // 桌面 Sim 兜底计算 grindor_hit_armor (41%/层，Android 由原生 GetArmorDR 结算)
        int arm_stacks = skill_count_buffs(tp, "grindor_hit_armor");
        if (arm_stacks > 0) {
            float dr = 0.41f * (float)arm_stacks;
            if (dr > 0.90f) dr = 0.90f;
            float apen = ctx->armor_penetration;
            if (apen < 0.0f) apen = 0.0f;
            if (apen > 1.0f) apen = 1.0f;
            ctx->modified_damage *= (1.0f - dr * (1.0f - apen));
        }
#endif

        // 受击被动：8% 护甲增益 (41%, 6s)，11% 对手暴击率减益 (-40%, 8s)
        int got_arm = 0, got_crit_deb = 0;
        if (skill_random_float() < 0.08f) {
            skill_apply_buff_dur(tp, "grindor_hit_armor", 6.0f);
            got_arm = 1;
        }
        if (ap >= 0 && ap < 2 && skill_random_float() < 0.11f) {
            skill_apply_buff_dur(ap, "grindor_struck_crit_debuff", 8.0f);
            got_crit_deb = 1;
        }
        if (got_arm || got_crit_deb) {
            skill_log("GRINDOR_PASSIVE: P%d struck -> armor_41=%d crit_debuff_40=%d",
                      tp, got_arm, got_crit_deb);
        }
    }

    // 2. 碾碎器作为攻击方
    if (ap >= 0 && ap < 2 && is_grindor(ctx->attacker_bot_id) && tp >= 0 && tp < 2) {
        float opp_mana_ratio = skill_get_mana(tp) / 3.0f;
        if (opp_mana_ratio < 0.0f) opp_mana_ratio = 0.0f;
        if (opp_mana_ratio > 1.0f) opp_mana_ratio = 1.0f;

        // 觉醒 贯穿：所有近战攻击（含 SP1/SP2/SP3 第 1 击）提升 110% * 敌方能量比例
        if (ctx->is_melee || (ctx->special_index >= 1 && ctx->hit_index == 0)) {
            if (opp_mana_ratio > 0.0f) {
                float perf_bonus = 1.10f * opp_mana_ratio;
                ctx->modified_damage *= (1.0f + perf_bonus);
                skill_log("GRINDOR_PERFORATE: P%d opp_mana=%.0f%% -> melee/sp_hit0 +%.1f%% dmg",
                          ap, opp_mana_ratio * 100.0f, perf_bonus * 100.0f);
            }
        }

        // SP2 增伤：依据对手当前能量最高 +40%
        if (ctx->special_index == 2 && opp_mana_ratio > 0.0f) {
            float sp2_bonus = 0.40f * opp_mana_ratio;
            ctx->modified_damage *= (1.0f + sp2_bonus);
            skill_log("GRINDOR_SP2_DMG: P%d opp_mana=%.0f%% -> SP2 +%.1f%% dmg",
                      ap, opp_mana_ratio * 100.0f, sp2_bonus * 100.0f);
        }

        // 格挡精通削弱：对手每层碾碎器暴击率减益降低 15% 格挡精通 (默认 50%)
        if (ctx->is_blocked) {
            int crit_debuffs = skill_count_buffs(tp, "grindor_struck_crit_debuff") +
                               skill_count_buffs(tp, "grindor_sp1_crit_debuff") +
                               skill_count_buffs(tp, "grindor_sp3_crit_debuff");
            if (crit_debuffs > 0) {
                float eff_bp = 0.50f - 0.15f * (float)crit_debuffs;
                if (eff_bp < 0.0f) eff_bp = 0.0f;
                float bp_scale = (1.0f - eff_bp) / 0.50f;
                ctx->modified_damage *= bp_scale;
                skill_log("GRINDOR_BLOCK_PROF: P%d vs blocking P%d (crit_debuffs=%d) -> eff_bp=%.0f%% dmg x%.2f",
                          ap, tp, crit_debuffs, eff_bp * 100.0f, bp_scale);
            }
        }

        // 非格挡触发：重击暴击燃烧 / SP1 / SP2 / SP3
        if (!ctx->is_blocked) {
            if (ctx->is_heavy && ctx->is_crit) {
                skill_apply_buff_dur(tp, "grindor_heavy_crit_burn", 6.0f);
                skill_log("GRINDOR_HEAVY_BURN: P%d Heavy crit inflicted 6.0s 80%% burn on P%d", ap, tp);
            } else if (ctx->special_index == 1 && ctx->is_last_hit) {
                skill_apply_buff_dur(tp, "grindor_sp1_crit_debuff", 8.0f);
                int locked2 = 0, locked3 = 0;
                if (skill_random_float() < 0.35f) {
                    skill_apply_buff_dur(tp, "grindor_sp1_disable_sp2", 6.0f);
                    locked2 = 1;
                }
                if (skill_random_float() < 0.75f) {
                    skill_apply_buff_dur(tp, "grindor_sp1_disable_sp3", 6.0f);
                    locked3 = 1;
                }
                if (locked2 || locked3) {
                    skill_overlay("[%s] 战术封锁！对手 %s%s 锁定6秒！",
                                  ap == 0 ? "碾碎器" : "敌方碾碎器",
                                  locked2 ? "SP2" : "",
                                  (locked2 && locked3) ? "+SP3" : (locked3 ? "SP3" : ""));
                }
                skill_log("GRINDOR_SP1: P%d crit_debuff(8s) lock_sp2=%d lock_sp3=%d on P%d",
                          ap, locked2, locked3, tp);
            } else if (ctx->special_index == 2 && ctx->is_last_hit) {
                if (skill_random_float() < 0.50f) {
                    skill_apply_buff_dur(tp, "grindor_sp2_disable_sp3", 6.0f);
                    skill_overlay("[%s] 战术封锁！对手 SP3 锁定6秒！",
                                  ap == 0 ? "碾碎器" : "敌方碾碎器");
                    skill_log("GRINDOR_SP2: P%d locked P%d SP3 for 6.0s", ap, tp);
                }
            } else if (ctx->special_index == 3 && ctx->is_last_hit) {
                skill_apply_buff_dur(tp, "grindor_sp3_disable_sp2", 10.0f);
                skill_apply_buff_dur(tp, "gp_disable_sp3_silent", 10.0f);
                skill_apply_buff_dur(tp, "grindor_sp3_crit_debuff", -1.0f);
                if (ctx->is_crit) {
                    skill_apply_buff_dur(tp, "grindor_sp3_crit_burn", 6.0f);
                }
                skill_overlay("[%s] 战术封锁！对手 SP2+SP3 锁定10秒！",
                              ap == 0 ? "碾碎器" : "敌方碾碎器");
                skill_log("GRINDOR_SP3: P%d locked P%d SP2+SP3(10s) + perm crit_debuff(crit=%d)",
                          ap, tp, ctx->is_crit ? 1 : 0);
            }
        }
    }
}

BotSkillModule g_module_grindor = {
    .bot_prefix          = "grindor",
    .display_name_zh     = "碾碎器",
    .on_hit_connected    = grindor_hit_connected,
    .on_crit_chance_mod  = grindor_crit_chance_mod,
};
